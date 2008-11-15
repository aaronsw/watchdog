import urllib, random, hmac, datetime
import simplejson as json
from hashlib import sha1

import web
import helpers, forms, config
from settings import db, render

def get_hexdigest(key, s):
    return hmac.new(key, s, sha1).hexdigest()

def encrypt_password(password):
    key = str(random.random())[2:]
    return '@'.join([key, get_hexdigest(key, password)])

def check_password(user, password):
    key, enc_password = user.password.split('@')
    return enc_password == get_hexdigest(key, password)

def loginuser(useremail, password):
    user = helpers.get_user_by_email(useremail)
    if user and check_password(user, password):
        helpers.set_login_cookie(useremail)
        return user
    else:
        return None

def new_user(email, password):
    token = get_secret_token(email)
    password = encrypt_password(password)
    exists = db.select('users', where='email=$email', vars=locals())
    if exists:
        return None

    user_id = db.insert('users', email=email, password=password, verified=True)
    user = web.storage(id=user_id, email=email, password=password, verified=True)
    return user
        
class signup:
    def POST(self):
        i = web.input(redirect='/')
        sf = forms.signupform()
        if not sf.validates(i):
            lf = forms.loginform()
            lf['redirect'].value = sf['redirect'].value = i.redirect
            sf.fill(i)
            return render.login(lf, sf, redirect=i.redirect)
        user = new_user(i.email, i.password)
        helpers.set_login_cookie(i.email)
        raise web.seeother(i.redirect, absolute=True)
      
def internal_redirect(path, method, query, data):
    # does an internal redirect within the application
    from webapp import app
    env = web.ctx.env
    env['REQUEST_METHOD'] = method
    env['PATH_INFO'] = path
    env['QUERY_STRING'] = web.utf8(query)

    cookie_headers = [(k, v) for k, v in web.ctx.headers if k == 'Set-Cookie'] 
    app.load(env)

    env['HTTP_COOKIE'] = env.get('HTTP_COOKIE', '') + ';' + ";".join([v for (k, v) in cookie_headers])
    web.ctx.headers = cookie_headers

    if method == 'POST':
        web.ctx.data = web.utf8(data)
    return app.handle()
         
class login:
    def GET(self):
        referer = web.ctx.env.get('HTTP_REFERER', '/')
        i = web.input(redirect=referer)
        lf, sf= forms.loginform(), forms.signupform()
        lf.fill(i)
        sf['redirect'].value = sf['redirect'].value = i.redirect
        msg, msg_type = helpers.get_delete_msg()
        return render.login(lf, sf, msg, i.redirect)

    def POST(self):
        i = web.input(redirect='/')
        lf = forms.loginform()
        if not lf.validates(i):
            sf = forms.signupform()
            lf['redirect'].value = sf['redirect'].value = i.redirect
            lf.fill(i)
            return render.login(lf, sf, redirect=i.redirect)
        else:
            state = i.get('state')
            if state:
                state = json.loads(state)
                return internal_redirect(state['redirect'], state['method'], state['query'], state['data'])
            else:    
                raise web.seeother(i.redirect, absolute=True)

class logout:
    def GET(self):
        return render.logout()

    def POST(self):
        helpers.del_login_cookie()
        helpers.del_unverified_cookie()
        referer = web.ctx.env.get('HTTP_REFERER', '/')
        raise web.seeother(referer)

def get_secret_token(email, validity=7):
    valid_till = (datetime.date.today() + datetime.timedelta(validity)).isoformat()
    return '@'.join([valid_till, helpers.encrypt(email + valid_till)])

def check_secret_token(email, token):
    valid_till, enc_email_ts = token.split('@')
    tampered = helpers.encrypt(email + valid_till) != enc_email_ts
    def expired():
        today = datetime.date.today()
        valid_date = datetime.date(*[int(t) for t in valid_till.split('-')])
        return today > valid_date

    return not(tampered or expired())

def set_password_url(email, token):
    query = urllib.urlencode(dict(email=email, token=token))
    url = 'http://watchdog.net/u/set_password?%s' % (query)
    return url

class forgot_password:
    def GET(self, form=None):
        form = form or forms.forgot_password()
        msg, msg_type = helpers.get_delete_msg()
        return render.forgot_password(form, msg)

    def POST(self):
        i = web.input()
        form = forms.forgot_password()
        if form.validates(i):
            token = get_secret_token(i.email)
            reset_url = set_password_url(i.email, token)
            subject = 'Reset your watchdog.net password'
            msg = """\
You asked to reset your password on watchdog.net.
You can do so at:

%s

but you have to do it within the next 7 days.

Thanks,
watchdog.net
""" % (reset_url)
            web.sendmail(config.from_address, i.email, subject, msg )
            helpers.set_msg('Check your email to reset your password.')
            raise web.seeother('/u/forgot_password', absolute=True)
        else:
            return self.GET(form)

class set_password:
    def GET(self, form=None):
        i = web.input()
        if check_secret_token(i.get('email', ''), i.get('token', '')):
            form = form or forms.passwordform()
            return render.set_password(form, i.email)
        else:
            helpers.set_msg('Invalid token', msg_type='error')
            raise web.seeother('/u/forgot_password', absolute=True)

    def POST(self):
        i = web.input()
        form = forms.passwordform()
        if form.validates(i):
            password = encrypt_password(i.password)
            db.update('users', password=password, verified=True, where='email=$i.email', vars=locals())
            helpers.set_login_cookie(i.email)
            helpers.set_msg('Password stored')
            raise web.seeother('/c/', absolute=True)
        else:
            return self.GET(form)

def send_mail_to_set_password(email):
    token = get_secret_token(email, validity=365)
    url = set_password_url(email, token)
    subject = 'Set your watchdog.net password'
    msg = """\
Thanks for using watchdog.net. We've created an account
for you with this email address -- but we don't have
a password for it. So that you can log in later, please
set your password at:

%s

If you've already set a password, then don't worry about
it and sorry for the interruption. If you think you received
this email in error, please hit reply and let us know.

Thanks,
watchdog.net
""" % (url)
    web.sendmail(config.from_address, email, subject, msg)

def assert_login(i=None):
    # let unlogged in users also do actions like signing, wyr
    # if the email has verified account with us but not logged-in, redirect to login form
    # if the email has unverified account, make them login and send set password email
    # if the email has no account, set an unverified account and send set password email
    i = i or web.input()
    email = i.email
    if helpers.get_loggedin_email():
        pass
    elif helpers.is_verified(email):
        login_page = do_login(email, set_state())
        raise web.webapi.HTTPError('200 OK', {}, data=str(login_page))
    else:
        helpers.unverified_login(email, i.get('fname'), i.get('lname'))
        send_mail_to_set_password(email)

def set_state():
    if web.ctx.method == 'POST':
        data = web.data()
    else:
        data = None
    query = web.ctx.env['QUERY_STRING']
    redirect = web.ctx.homepath + web.ctx.path
    method = web.ctx.method
    return dict(redirect=redirect, query=query, method=method, data=data)
    
def do_login(email, state):
    lf, sf = forms.loginform(), forms.signupform()
    lf.fill(useremail=email, redirect=state['redirect'], state=json.dumps(state))
    sf.fill(redirect=state['redirect'], state=state)
    return render.login(lf, sf)
    
def require_login(f):
    def g(*a, **kw):
        if not helpers.get_loggedin_email():
            query = urllib.urlencode(dict(redirect=web.ctx.homepath + web.ctx.fullpath))
            raise web.seeother("/u/login?%s" % (query), absolute=True)
        return f(*a, **kw)
    return g
