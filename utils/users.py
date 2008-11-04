import web
from settings import db, render
import forms, helpers, auth
from contacts import importcontacts
from auth import login, signup, logout, forgot_password, set_password
import urllib

urls = (
    '/login', 'login',
    '/logout', 'logout',
    '/signup', 'signup',
    '/set_password', 'set_password',
    '/forgot_password', 'forgot_password',
    '/import_contacts', 'importcontacts',
    r'/(\d+)', 'petitions',
    r'/(\d+)/preferences', 'userinfo',
    )
    
def fill_user_details(form, fillings=['email', 'name', 'contact']):
    details = {}
    email = helpers.get_loggedin_email() or helpers.get_unverified_email()
    if email:
        if 'email' in fillings:
            details['email'] = email

        user = db.select('users', where='email=$email', vars=locals())
        if user:
            user = user[0]
            if 'name' in fillings:
                details['userid'] = user.id
                details['prefix'] = user.prefix
                details['fname'] = user.fname
                details['lname'] = user.lname
            if 'contact' in fillings:
                details['addr1'] = user.addr1
                details['addr2'] = user.addr2
                details['city'] = user.city
                details['zipcode'] = user.zip5
                details['zip4'] = user.zip4
                details['phone'] = user.phone
                details['state'] = user.state

        form.fill(**details)
    
def update_user_details(i):
    user = helpers.get_user_by_email(i.get('email'))
    userid = user and user.id
    i['zip5'] = i.get('zipcode')
    i['phone'] = web.numify(i.get('phone'))
    details = ['prefix', 'lname', 'fname', 'addr1', 'addr2', 'city', 'zip5', 'zip4', 'phone', 'state']
    
    d = {}
    for (k, v) in i.items():
        if v and (k in details): 
            d[k] = v
    db.update('users', where='id=$userid', vars=locals(), **d)
    
def get_password_form(user):
    #if the user has already set a password before, add the current password field to the form.
    form = forms.change_password()
    if user.password:
        curr_password = forms.curr_password
        form.inputs = (curr_password, ) + form.inputs
    return form    


def check_permission(uid):
    current_uid = helpers.get_loggedin_userid()
    if current_uid != int(uid):
        query = urllib.urlencode(dict(redirect=web.ctx.homepath + web.ctx.fullpath))
        raise web.seeother("/u/login?%s" % (query), absolute=True)

def created_by(uid):
    created = db.select('petition',
            where='owner_id=$uid and petition.deleted is null',
            order='created desc',
            vars=locals())
    return created

def signed_by(uid):
    signed = db.select('signatory, petition', what='petition.id, title, signed, comment',
            where='user_id=$uid and \
                   petition.id = signatory.petition_id and \
                   petition.deleted is null',
            order='signed desc',
            vars=locals())
    return signed

class petitions():
    def GET(self, uid):
        from petition import get_num_signs
        user = db.select('users', what='id, lname, fname', where='id=$uid', vars=locals())      
        if not user: raise web.notfound
        created, signed = created_by(uid).list(), signed_by(uid).list()
        for p in created + signed: p.signcount = get_num_signs(p.id)
        logged_in = (helpers.get_loggedin_userid() == int(uid))
        return render.user_petitions(user[0], created, signed, logged_in)

class userinfo():
    def GET(self, uid, info_form=None, password_form=None):
        check_permission(uid)
        try:
            user = db.select('users', where='id=$uid', vars=locals())[0]
        except IndexError:     
            raise web.notfound
        
        info_form = info_form or forms.userinfo()
        if not password_form:
            password_form = get_password_form(user)
            
        info_form.fill(**user)
        msg, msg_type = helpers.get_delete_msg()
        return render.userpage(uid, info_form, password_form, msg)

    def POST(self, uid):
        i = web.input('m', _method='GET')
        if i.m == 'password':
            return self.POST_password(uid)
        
        form = forms.userinfo()
        i = web.input(_method='POST')
        if form.validates(i):
            if 'submit' in i: i.pop('submit')
            db.update('users', where='id=$uid', vars=locals(), **i)
            helpers.set_msg('User information updated.')
            raise web.seeother('/%s/preferences' % uid)
        else:
            return self.GET(uid, info_form=form)
    
    def POST_password(self, uid):
        user = db.select('users', what='password', where='id=$uid', vars=locals())[0]
        form = get_password_form(user)
        set_passwd_form = 'curr_password' not in [inp.name for inp in list(form.inputs)]
        i = web.input()
        if form.validates(i):
            if set_passwd_form or auth.check_password(user, i.curr_password):
                enc_password = auth.encrypt_password(i.password)
                db.update('users', password=enc_password, verified=True, where='id=$uid', vars=locals())
                helpers.set_msg('Password %s.' % ('saved' if set_passwd_form else 'changed'))
                raise web.seeother('/%s/preferences' % uid)
            else:
                helpers.set_msg('Invalid Password', 'error')    
                form.note = 'Current Password invalid.'
                form.valid = False
        return self.GET(uid, password_form=form)   
            
app = web.application(urls, globals())
if __name__ == '__main__':
    app.run()            