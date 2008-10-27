
from __future__ import with_statement

import web
from utils import forms, helpers, auth
from settings import db, render, render_plain, session
from utils.auth import require_login
from utils.users import fill_user_details, update_user_details
import config
from utils.wyrutils import CaptchaException, add_captcha

from datetime import datetime

urls = (
  '', 'redir',
  '/', 'index',
  '/new', 'new',
  '/login', 'login',
  '/signup', 'signup',
  '/verify', 'checkID',
  '/(.*)/signatories', 'signatories',
  '/(.*)', 'petition'
)

class redir:
    def GET(self): raise web.seeother('/')

class checkID:
    def POST(self):
        "Return True if petition with id `pid` does not exist"
        pid = web.input().pid
        exists = bool(db.select('petition', where='id=$pid', vars=locals()))
        return pid != 'new' and not(exists)

class index:
    def GET(self):
        petitions = db.select(['petition', 'signatory'],
                    what='petition.id, petition.title, count(signatory.user_id) as signature_count',
                    where='petition.id = signatory.petition_id and petition.deleted is null',
                    group='petition.id, petition.title',
                    order='count(signatory.user_id) desc'
                    )

        msg, msg_type = helpers.get_delete_msg()
        return render.petition_list(petitions, msg)

def send_to_congress(i, wyrform, signid=None):
    from utils.writerep import write_your_rep
    
    pform, wyrform = forms.petitionform(), (wyrform or forms.wyrform())
    pform.fill(i), wyrform.fill(i)
    wyr = write_your_rep()
    wyr.set_pol(i)
    if not signid: signid = get_signid(i.pid)
    wyr.set_msg_id(signid, petition=True)
    msg_sent = wyr.send_msg(i, wyrform, pform)
    sent_status = msg_sent and 'S' or 'D'   # Sent or Due for sending
    db.update('signatory', where='id=$signid', sent_to_congress=sent_status, vars=locals())
    
def captcha_to_be_filled(i):    
    from utils.wyrutils import getdists, has_captcha, dist2pol
    dist = getdists(i.zipcode, i.zip4, i.addr1+i.addr2)[0]
    return has_captcha(dist2pol(dist))

def get_signid(pid):
    uemail = helpers.get_loggedin_email() or helpers.get_unverified_email()
    user = helpers.get_user_by_email(uemail)
    uid = user and user.id
    try:    
        sign = db.select('signatory', what='id', 
                    where="petition_id=$pid and user_id=$uid",
                    vars=locals())[0]
    except IndexError:
        pass
    else:                    
        return sign.id
        
def create_petition(i, email, wyrform):
    tocongress = i.get('tocongress', 'off') == 'on'
    i.pid = i.pid.replace(' ', '_')
    u = helpers.get_user_by_email(email)
    try:
        db.insert('petition', seqname=False, id=i.pid, title=i.ptitle, description=i.msg,
                owner_id=u.id, to_congress=tocongress)
    except:
        return
    signid = save_signature(i, i.pid, u.id, tocongress)            

    if tocongress and captcha_to_be_filled(i): wyrform.fill(signid=signid)
    if tocongress: send_to_congress(i, wyrform, signid)

    msg = """Congratulations, you've created your petition.
             Now sign and share it with all your friends."""
    helpers.set_msg(msg)
    
class new:
    def GET(self, wyrform=None):
        pform = forms.petitionform()
        cform = wyrform or forms.wyrform()
        fill_user_details(cform)
        add_captcha(cform)
        email = helpers.get_loggedin_email() or helpers.get_unverified_email()
        return render.petitionform(pform, cform)

    def POST(self, input=None):
        i = input or web.input()
        tocongress = i.get('tocongress', 'off') == 'on'
        pform, wyrform = forms.petitionform(), forms.wyrform()
        i.email = 'one@valid.mail' # to make wyrform valid, find a better work around
        wyr_valid = (not(tocongress) or wyrform.validates(i))
        
        if 'signid' in i:
            signid = i.signid
            send_to_congress(i, wyrform, signid)
            raise web.seeother('/%s' % i.pid)
            
        if not pform.validates(i) or not wyr_valid:
            return render.petitionform(pform, wyrform)

        email = helpers.get_loggedin_email()
        if not email:
            return login().GET(i)

        try:    
            create_petition(i, email, wyrform)
        except CaptchaException:
            msg, msg_type = helpers.get_delete_msg()
            return render.petitionform(pform, wyrform, msg) 
               
        raise web.seeother('/%s' % i.pid)

class login:
    def GET(self, i, wf=None):
        lf, sf = forms.loginform(), forms.signupform()
        pf, wf = forms.petitionform(), (wf or forms.wyrform())
        pf.fill(i), wf.fill(i)
        return render.petitionlogin(lf, sf, pf, wf)

    def POST(self):
        i = web.input()
        lf, wf =  forms.loginform(), forms.wyrform()
        if not lf.validates(i):
            pf, sf = forms.petitionform(), forms.signupform()
            lf.fill(i), pf.fill(i), wf.fill(i)
            return render.petitionlogin(lf, sf, pf, wf)
            
        try:    
            create_petition(i, i.useremail, wf)
        except CaptchaException:
            msg, msg_type = helpers.get_delete_msg()
            pf= forms.petitionform()
            pf.fill(i)
            return render.petitionform(pf, wf, msg)    
            
        raise web.seeother('/%s' % i.pid)

class signup:
    def POST(self):
        i = web.input()
        sf, wf = forms.signupform(), forms.wyrform()
        if not sf.validates(i):
            lf, pf = forms.loginform(), forms.petitionform()
            sf.fill(i), pf.fill(i), wf.fill(i)
            return render.petitionlogin(lf, sf, pf, wf)
        user = auth.new_user(i.email, i.password)
        helpers.set_login_cookie(i.email)
        try:
            create_petition(i, i.email, wf)
        except CaptchaException:
            msg, msg_type = helpers.get_delete_msg()
            pf = forms.petitionform()
            pf.fill(i)
            return render.petitionform(pf, wf, msg)
            
        raise web.seeother('/%s' % i.pid)

def askforpasswd(user_id):
    useremail = helpers.get_loggedin_email()
    #if the current user is the owner of the petition and has not set the password
    r = db.select('users', where='id=$user_id AND email=$useremail AND password is NULL', vars=locals())
    return bool(r)

def save_password(forminput):
    password = auth.encrypt_password(forminput.password)
    db.update('users', where='id=$forminput.user_id', password=password, vars=locals())
    helpers.set_msg('Password stored')

def save_signature(i, pid, uid, tocongress=False):
    has_captcha = tocongress and captcha_to_be_filled(i)
    msg_status = has_captcha and 'T' #mark it as temporary
    msg_status = msg_status or (tocongress and 'D') or 'N' # D=sending due; N=not for congress  

    where = 'petition_id=$pid AND user_id=$uid and deleted is null'
    signed = db.select('signatory', where=where, vars=locals())
    share_with = (i.get('share_with', 'off') == 'on' and 'N') or 'A'
    if not signed:
        referrer = get_referrer(pid, uid)
        signid = db.insert('signatory', 
                user_id=uid, share_with=share_with,
                petition_id=pid, comment=i.get('comment'),
                sent_to_congress=msg_status, referrer=referrer)
        update_user_details(i)
        helpers.set_msg("Thanks for your signing! Why don't you tell your friends about it now?")
        return signid 
    else:
        if not signed[0].sent_to_congress == 'T':
            helpers.set_msg("You've signed this petition before. Why don't you tell your friends about it now?")
        
def sendmail_to_signatory(user, pid):
    p = get_petition_by_id(pid)
    p.url = 'http://watchdog.net/c/%s' % (pid)
    token = auth.get_secret_token(user.email)
    msg = render_plain.signatory_mailer(user, p, token)
    #@@@ shouldn't this web.utf8 stuff taken care by in web.py?
    web.sendmail(web.utf8(config.from_address), web.utf8(user.email), web.utf8(msg.subject.strip()), web.utf8(msg))

def is_author(email, pid):
    user = email and helpers.get_user_by_email(email)
    where = 'id=$pid and owner_id=$user.id and deleted is null'
    return user and bool(db.select('petition', where=where, vars=locals()))

def is_signatory(email, pid):
    user = email and helpers.get_user_by_email(email)
    where = 'petition_id=$pid and user_id=$user.id'
    return user and bool(db.select('signatory', where=where, vars=locals()))
    
def get_signs(pid):
    where = "petition_id=$pid AND users.id=user_id AND sent_to_congress !='T' AND deleted is null"          
    return db.select(['signatory', 'users'],
                        what='users.fname, users.lname, users.email, '
                              'signatory.share_with, signatory.comment, '
                              'signatory.signed',
                        where=where,
                        order='signed desc',
                        vars=locals())

def to_congress(pid):
    return bool(db.select("petition", where="id=$pid AND to_congress='t'", vars=locals()))

def get_num_signs(pid):
    where = "petition_id=$pid AND sent_to_congress != 'T' AND deleted is null"
    r = db.query("select count(*) from signatory where " + where, vars=locals())
    return r[0].count
                       
def get_petition_by_id(pid):
    try:
        return db.select('petition', where='id=$pid and deleted is null', vars=locals())[0]
    except IndexError:
        return                            

class signatories:
    def GET(self, pid):
        user_email = helpers.get_loggedin_email()
        p = get_petition_by_id(pid)
        if not p: raise web.notfound
        ptitle = p.title
        signs = get_signs(pid).list()
        return render.signature_list(pid, ptitle, signs, is_author(user_email, pid))
                        
def set_referrer_cookie(tid, pid):
    if helpers.check_trackid(tid, pid):
        helpers.setcookie('tid', tid)

def get_referrer(pid, uid):
    tid = helpers.getcookie('tid')
    referrer = helpers.check_trackid(tid, pid)
    if referrer != uid:
        return referrer

class petition:
    def GET(self, pid, signform=None, wyrform=None):
        i = web.input()
        p = get_petition_by_id(pid)
        if not p: raise web.notfound
        
        options = ['unsign', 'edit', 'delete']
        if i.get('m', None) in options:
            handler = getattr(self, 'GET_'+i.m)
            return handler(pid)

        p.signatory_count = get_num_signs(pid)
        if not signform:
            signform = forms.signform()
            fill_user_details(signform)
            
        if to_congress(pid) and not wyrform:
            wyrform = forms.wyrform()
            fill_user_details(wyrform)
            add_captcha(wyrform)

        if 'tid' in i: 
            set_referrer_cookie(i.tid, pid)
            raise web.seeother('/%s' % pid)
            
        msg, msg_type = helpers.get_delete_msg()
        useremail = helpers.get_loggedin_email() or helpers.get_unverified_email()
        isauthor = is_author(useremail, pid)
        issignatory = is_signatory(useremail, pid)
        return render.petition(p, signform, useremail, isauthor, issignatory, wyrform, msg)

    @auth.require_login
    def GET_edit(self, pid):
        user_email = helpers.get_loggedin_email()
        if is_author(user_email, pid):
            p = get_petition_by_id(pid)
            u = helpers.get_user_by_email(user_email)
            pform = forms.petitionform()
            pform.fill(userid=u.id, email=user_email, pid=p.id, ptitle=p.title, msg=p.description, tocongress=p.to_congress)
            cform = forms.wyrform()
            fill_user_details(cform)
            title = "Edit your petition"
            return render.petitionform(pform, cform, title, target='/c/%s?m=edit' % (pid))
        else:
            login_link = '<a href="/u/login">Login</a>'
            helpers.set_msg('Only author of this petition can edit it. %s if you are.' % login_link, msg_type='error')
            raise web.seeother('/%s' % pid)


    def GET_unsign(self, pid):
        i = web.input()
        user = helpers.get_user_by_email(i.email)

        if user:
            where = 'petition_id=$pid and user_id=$user.id and deleted is null'
            signatory = db.select('signatory', where=where, vars=locals())

        valid_token = auth.check_secret_token(i.get('email'), i.get('token'))
        if not (user and signatory and valid_token):
            msg = "Invalid token or there is no signature for this petition with this email."
            msg_type = 'error'
        else:
            msg = render_plain.confirm_unsign(pid, user.id)
            msg_type = ''

        helpers.set_msg(msg, msg_type)
        raise web.seeother('/%s' % pid)

    def GET_delete(self, pid):
        user_email = helpers.get_loggedin_email()
        if is_author(user_email, pid):
            msg = str(render_plain.confirm_deletion(pid))
            helpers.set_msg(msg)
        else:
            login_link = '<a href="/u/login">Login</a>'
            helpers.set_msg('Only author of this petition can delete it. %s if you are.' % login_link, msg_type='error')

        raise web.seeother('/%s' % pid)

    def POST(self, pid):
        i = web.input('m', _method='GET')
        options = ['sign', 'unsign', 'edit', 'password', 'delete']
        if i.m in options:
            handler = getattr(self, 'POST_'+i.m)
            return handler(pid)
        else:
            raise ValueError

    def POST_password(self, pid):
        form = forms.passwordform()
        i = web.input()
        if form.validates(i):
            save_password(i)
            raise web.seeother('/%s' % pid)
        else:
            return self.GET(pid, passwordform=form)

    def POST_sign(self, pid):
        i = web.input()
        sform = forms.signform()
        tocongress = to_congress(pid)
        p = get_petition_by_id(pid)
                
        if tocongress:
            i.pid, i.ptitle, i.msg = pid, p.title, p.description
            wyrform = forms.wyrform()
            wyr_valid =  wyrform.validates(i)
        else:
            wyrform, wyr_valid = None, True

        if sform.validates(i) and wyr_valid:
            auth.assert_login(i)
            user = helpers.get_user_by_email(i.email)
            signid = save_signature(i, pid, user.id, tocongress)
            if tocongress: 
                try:
                    i.msg = "%s\n%s" %(i.msg, i.comment) #need to compose 
                    msg_sent = send_to_congress(i, wyrform, signid)
                except CaptchaException:
                    return self.GET(pid, signform=sform, wyrform=wyrform)    
            if signid:
                sendmail_to_signatory(user, pid)
            raise web.seeother('/share?url=/c/%s&title=%s' % (pid, p.title), absolute=True)
        else:
            return self.GET(pid, signform=sform, wyrform=wyrform)

    @auth.require_login
    def POST_edit(self, pid):
        i = web.input()
        tocongress = i.get('tocongress', 'off') == 'on'
        pform = forms.petitionform()
        pform.inputs = filter(lambda i: i.name != 'pid', pform.inputs)
        wyrform = forms.wyrform()
        i.email = helpers.get_loggedin_email()
        wyr_valid = (not(tocongress) or wyrform.validates(i))
        if not pform.validates(i) or not wyr_valid:
            title = "Edit petition"
            return render.petitionform(pform, wyrform, title, target='/c/%s?m=edit' % (pid))
        db.update('petition', where='id=$pid', title=i.ptitle, description=i.msg, to_congress=tocongress, vars=locals())
        update_user_details(i)
        raise web.seeother('/%s' % pid)

    def POST_unsign(self, pid):
        i = web.input()
        now = datetime.now()
        db.update('signatory',
                        deleted=now,
                        where='petition_id=$pid and user_id=$i.user_id',
                        vars=locals())
        msg = 'Your signature has been removed for this petition.'
        helpers.set_msg(msg)
        raise web.seeother('/%s' % pid)

    def POST_delete(self, pid):
        now = datetime.now()
        title = db.select('petition', what='title', where='id=$pid', vars=locals())[0].title
        db.update('petition', where='id=$pid', deleted=now, vars=locals())
        helpers.set_msg('Petition "%s" deleted' % (title))
        raise web.seeother('/')

def get_contacts(user, by='id'):
    if by == 'email':
        where = 'uemail=$user'
    else:
        where = 'user_id=$user'

    contacts = db.select('contacts',
                    what='cname as name, cemail as email, provider',
                    where=where,
                    vars=locals()).list()

    if by == 'id':
        #remove repeated emails due to multiple providers; prefer the one which has name
        cdict = {}
        for c in contacts:
            if c.email not in cdict.keys():
                cdict[c.email] = c
            elif c.name:
                cdict[c.email] = c
        contacts = cdict.values()

    for c in contacts:
        c.name = c.name or c.email.split('@')[0]

    contacts.sort(key=lambda x: x.name.lower())
    return contacts

def signed(email, pid):
    try:
        user_id = db.select('users', what='id', where='email=$email', vars=locals())[0].id
    except IndexError:
        return False
    else:
        is_signatory = db.select('signatory', where='user_id=$user_id and petition_id=$pid', vars=locals())
        return bool(is_signatory)


class share:
    def GET(self, emailform=None, loadcontactsform=None):
        i = web.input()
        url = i.get('url', '/')
        title = i.get('title', 'The good government site with teeth')

        user_id = helpers.get_loggedin_userid()
        contacts = get_contacts(user_id)
        if (not contacts) and ('email' in session):
            contacts = get_contacts(session.get('email'), by='email')

        page_or_petition = 'page'    
        if not emailform:
            emailform = forms.emailform()
            track_id, description = None, None
            if url.startswith('/c/') and url != '/c/':
                url = url.rstrip('/')
                pid = web.lstrips(url, '/c/')
                p = get_petition_by_id(pid)
                description = p and p.description
                track_id = helpers.get_trackid(user_id, pid)
                contacts = filter(lambda c: not signed(c.email, pid), contacts)
                page_or_petition = 'petition'

            msg = render_plain.share_mail(title, url, description, track_id)
            emailform.fill(subject=title, body=msg)

        loadcontactsform = loadcontactsform or forms.loadcontactsform()

        msg, msg_type = helpers.get_delete_msg()
        return render.share(title, url, emailform,
                            contacts, loadcontactsform, page_or_petition, msg)

    def POST(self):
        i = web.input()
        emailform, loadcontactsform = forms.emailform(), forms.loadcontactsform()
        if emailform.validates(i):
            url, msg, subject = i.url, i.body, i.subject
            emails = [e.strip() for e in i.emails.strip(', ').split(',')]
            u = helpers.get_user_by_email(helpers.get_loggedin_email())
            from_address = u and "%s %s <%s>" % (u.fname, u.lname, u.email) or config.from_address
            web.sendmail(from_address, emails, subject, msg)
            page_or_petition = url.startswith('/c/') and 'petition' or 'page'
            helpers.set_msg('Thanks for sharing this %s with your friends!' % page_or_petition)
            raise web.seeother(url)
        else:
            return self.GET(emailform=emailform, loadcontactsform=loadcontactsform)

app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
