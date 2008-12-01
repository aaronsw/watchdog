
from __future__ import with_statement

import web
from utils import forms, helpers, auth, wyrapp
from settings import db, render, render_plain
from utils.auth import require_login
from utils.users import fill_user_details, update_user_details
from utils.writerep import require_captcha, send_msgs
import config

from datetime import datetime
import urllib

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

def send_to_congress(uid, i, signid):
    #@@@ compose here too
    i.msg = i.msg + '\n' + i.get('comment', '')
    send_msgs(uid, i, source_id='s%s' % signid)
        
def create_petition(i, email):
    tocongress = i.get('tocongress', 'off') == 'on'
    i.pid = i.pid.replace(' ', '-')
    u = helpers.get_user_by_email(email)
    try:
        db.insert('petition', seqname=False, id=i.pid, title=i.ptitle,
                    description=i.msg, owner_id=u.id, to_congress=tocongress)
    except: return
    signid = save_signature(i, i.pid, u.id)
    if tocongress: send_to_congress(u.id, i, signid)
    msg = """Congratulations, you've created your petition.
             Now sign and share it with all your friends."""
    helpers.set_msg(msg)
    
class new:
    def GET(self, pf=None, wf=None):
        pf = pf or forms.petitionform()
        if not wf:
            #create a new form and initialize with current user details
            wf = forms.wyrform()
            u = helpers.get_user()
            u and fill_user_details(wf, u)
        captcha_html = wyrapp.prepare_for_captcha(wf)
        msg, msg_type = helpers.get_delete_msg()
        return render.petitionform(pf, wf, captchas=captcha_html, msg=msg)

    def POST(self):
        i = web.input()
        tocongress = i.get('tocongress', 'off') == 'on'
        pf, wf = forms.petitionform(), forms.wyrform()
        i.email = 'one@valid.mail' # to make wf valid, find a better work around
        wyr_valid = (not(tocongress) or wf.validates(i))
        captcha_needed = require_captcha(i)
        wyr_valid = wyr_valid and not captcha_needed

        if not pf.validates(i) or not wyr_valid:
            if captcha_needed: wf.valid, wf.note = False, 'Please Fill the captcha below'
            pf.fill(i), wf.fill(i)
            return self.GET(pf, wf)

        email = helpers.get_loggedin_email()
        if not email:
            return login().GET(i)

        create_petition(i, email)
        raise web.seeother('/%s' % i.pid)

class login:
    def GET(self, i=None, wf=None):
        i = i or web.input()
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
        create_petition(i, i.useremail)
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
        create_petition(i, i.email)    
        raise web.seeother('/%s' % i.pid)

def save_signature(i, pid, uid):
    where = 'petition_id=$pid AND user_id=$uid'
    signed = db.select('signatory', where=where, vars=locals())
    share_with = (i.get('share_with', 'off') == 'on' and 'N') or 'A'
    update_user_details(i)
    if not signed:
        referrer = get_referrer(pid, uid)
        signid = db.insert('signatory', user_id=uid, share_with=share_with,
                petition_id=pid, comment=i.get('comment'), referrer=referrer)
        helpers.set_msg("Thanks for your signing! Why don't you tell your friends about it now?")
        return signid
    else:
        db.update('signatory', where='user_id=$uid and petition_id=$pid', 
                    comment=i.get('comment'), deleted=None, vars=locals())
        helpers.set_msg("Your signature has been changed. Why don't you tell your friends about it now?")
        return 'old_%s' % signed[0].id
  
def sendmail_to_signatory(user, pid):
    """sends a thanks mail to the user, with request to share the petition with friends.
    """
    p = get_petition_by_id(pid)
    p.url = 'http://watchdog.net/c/%s' % (pid)
    token = auth.get_secret_token(user.email)
    msg = render_plain.signatory_mailer(user, p, token)
    web.sendmail(config.from_address, user.email, msg.subject.strip(), str(msg))

def is_author(email, pid):
    user = email and helpers.get_user_by_email(email)
    where = 'id=$pid and owner_id=$user.id and deleted is null'
    return user and bool(db.select('petition', where=where, vars=locals()))

def is_signatory(email, pid):
    user = email and helpers.get_user_by_email(email)
    where = 'petition_id=$pid and user_id=$user.id and deleted is null'
    return user and bool(db.select('signatory', where=where, vars=locals()))
    
def get_signs(pid):
    where = "petition_id=$pid AND users.id=user_id AND deleted is null" 
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
    where = "petition_id=$pid AND deleted is null"
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
    def GET(self, pid, sf=None, wf=None):
        i = web.input()
        pid = pid.rstrip('/')
        p = get_petition_by_id(pid)
        if not p: raise web.notfound
        
        options = ['unsign', 'edit', 'delete']
        if i.get('m', None) in options:
            handler = getattr(self, 'GET_'+i.m)
            return handler(pid)

        if not sf:
            sf = forms.signform()
            fill_user_details(sf)

        captcha_html = ''
        if to_congress(pid):
            if not wf:
                wf = forms.wyrform()
                fill_user_details(wf)
            captcha_html = wyrapp.prepare_for_captcha(wf)    

        if 'tid' in i: 
            set_referrer_cookie(i.tid, pid)
            raise web.seeother('/%s' % pid)
            
        useremail = helpers.get_loggedin_email() or helpers.get_unverified_email()
        isauthor = is_author(useremail, pid)
        issignatory = is_signatory(useremail, pid)
        p.signatory_count = get_num_signs(pid)
        msg, msg_type = helpers.get_delete_msg()
        return render.petition(p, sf, useremail, isauthor, issignatory, wf, captcha_html, msg)

    @auth.require_login
    def GET_edit(self, pid):
        user_email = helpers.get_loggedin_email()
        if is_author(user_email, pid):
            p = get_petition_by_id(pid)
            u = helpers.get_user_by_email(user_email)
            pf = forms.petitionform()
            pf.fill(userid=u.id, email=user_email, pid=p.id, ptitle=p.title, msg=p.description, tocongress=p.to_congress)
            wf = forms.wyrform()
            fill_user_details(wf)
            title = "Edit your petition"
            return render.petitionform(pf, wf, title, target='/c/%s?m=edit' % (pid))
        elif user_email:
            msg = "You don't have permissions to edit this petition."
        else:    
            login_link = '<a href="/u/login">Login</a>'
            msg = 'Only author of this petition can edit it. %s if you are.' % login_link
        helpers.set_msg(msg)
        raise web.seeother('/%s' % pid)


    def GET_unsign(self, pid):
        i = web.input()
        user = helpers.get_user_by_email(i.email)

        if user:
            where = 'petition_id=$pid and user_id=$user.id and deleted is null'
            signatory = db.select('signatory', where=where, vars=locals())

        valid_token = auth.check_secret_token(i.get('email', ''), i.get('token', '@'))
        if not (user and signatory and valid_token):
            msg = "Invalid token or there is no signature for this petition with this email."
            msg_type = 'error'
        else:
            msg = str(render_plain.confirm_unsign(pid, user.id))
            msg_type = ''

        helpers.set_msg(msg, msg_type)
        raise web.seeother('/%s' % pid)

    def GET_delete(self, pid):
        user_email = helpers.get_loggedin_email()
        if is_author(user_email, pid):
            msg = str(render_plain.confirm_deletion(pid))
        elif user_email:
            msg = "You don't have permissions to delete this petition."
        else:    
            login_link = '<a href="/u/login">Login</a>'
            msg = 'Only author of this petition can delete it. %s if you are.' % login_link
        helpers.set_msg(msg)
        raise web.seeother('/%s' % pid)

    def POST(self, pid):
        i = web.input('m', _method='GET')
        options = ['sign', 'unsign', 'edit', 'delete']
        if i.m in options:
            handler = getattr(self, 'POST_'+i.m)
            return handler(pid)
        else:
            raise ValueError

    def POST_sign(self, pid):
        i = web.input()
        sf = forms.signform()
        tocongress = to_congress(pid)
        p = get_petition_by_id(pid)
        
        is_new = lambda sid: not isinstance(sid, str)
        get_new = lambda sid: int(web.lstrips(sid, 'old_'))
        if tocongress:
            i.pid, i.ptitle, i.msg = pid, p.title, p.description
            wf = forms.wyrform()
            captcha_needed = require_captcha(i)
            wyr_valid =  wf.validates(i) and not captcha_needed
            if captcha_needed: wf.valid, wf.note = False, 'Please fill the captcha below'
        else:
            wf, wyr_valid = None, True

        if sf.validates(i) and wyr_valid:
            uid = auth.assert_login(i)
            signid = save_signature(i, pid, uid)
            if is_new(signid):
                user = helpers.get_user_by_id(uid)
                sendmail_to_signatory(user, pid)
            else:
                signid = get_new(signid)
            if tocongress: send_to_congress(uid, i, signid)
            query = urllib.urlencode(dict(url='/c/%s' % pid, title=p.title))
            raise web.seeother('/share?%s' % query, absolute=True)
        else:
            return self.GET(pid, sf=sf, wf=wf)

    @auth.require_login
    def POST_edit(self, pid):
        i = web.input()
        tocongress = i.get('tocongress', 'off') == 'on'
        pf = forms.petitionform()
        pf.inputs = filter(lambda i: i.name != 'pid', pf.inputs)
        wf = forms.wyrform()
        i.email = helpers.get_loggedin_email()
        wyr_valid = (not(tocongress) or wf.validates(i))
        if not pf.validates(i) or not wyr_valid:
            title = "Edit petition"
            return render.petitionform(pf, wf, title, target='/c/%s?m=edit' % (pid))
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

class share:
    def GET(self, emailform=None, loadcontactsform=None):
        i = web.input()
        url = i.get('url', '/')
        title = i.get('title', 'The good government site with teeth')

        user_id = helpers.get_loggedin_userid()
        contacts = get_contacts(user_id)
        sender = helpers.get_user_by_email(helpers.get_loggedin_email() or helpers.get_unverified_email())

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
                contacts = filter(lambda c: not is_signatory(c.email, pid), contacts)
                page_or_petition = 'petition'

            msg = render_plain.share_mail(title, url, sender, description, track_id)
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
            u = helpers.get_user_by_email(helpers.get_loggedin_email() or helpers.get_unverified_email())
            from_address = u and "%s %s <%s>" % (u.fname, u.lname, u.email) or config.from_address
            for email in emails:
                web.sendmail(from_address, email, subject, msg)
            page_or_petition = url.startswith('/c/') and 'petition' or 'page'
            helpers.set_msg('Thanks for sharing this %s with your friends!' % page_or_petition)
            raise web.seeother(url)
        else:
            return self.GET(emailform=emailform, loadcontactsform=loadcontactsform)

app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
