
from __future__ import with_statement

import web
from utils import forms, helpers, auth
from settings import db, render
import config

from datetime import datetime

urls = (
  '', 'redir',
  '/', 'index',
  '/new', 'new', 
  '/verify', 'checkID',
  '/(.*)/share', 'share',
  '/(.*)/signatories', 'signatories',
  '/(.*)', 'petition'
)

render_plain = web.template.render('templates/') #without base, useful for sending mails

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
        return render.petition_list(petitions)
        
def save_petition(p):
    p.pid = p.pid.replace(' ', '_')
    with db.transaction():
        try:
            owner = db.select('users', where='email=$p.email', vars=locals())[0]
        except:
            owner_id = db.insert('users', email=p.email, 
                                prefix=p.prefix, lname=p.lname, fname=p.fname, 
                                addr1=p.addr1, addr2=p.addr2, phone=p.phone,
                                city=p.city, zip5=p.zipcode, 
                                verified=True) 
        else:
            if not owner.verified: db.update('users', where='email=$p.email', verified=True, vars=locals())
            owner_id = owner.id
            
        db.insert('petition', seqname=False, id=p.pid, title=p.ptitle, description=p.msg,
                    owner_id=owner_id)
        #make the owner of the petition sign for it (??)             
        db.insert('signatory', user_id=owner_id, share_with='E', petition_id=p.pid)      
        
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
                details['prefix'] = user.prefix
                details['fname'] = user.fname
                details['lname'] = user.lname    
            if 'contact' in fillings:
                details['prefix'] = user.prefix
                details['addr1'] = user.addr1
                details['addr2'] = user.addr2
                details['city'] = user.city
                details['zipcode'] = user.zip5
                details['phone'] = user.phone    
                if filter(lambda i: i.name == 'zip4', form.inputs):
                    details['zip4'] = user.zip4   
    form.fill(**details)

    
    if helpers.get_loggedin_email():
        for i in form.inputs:
            if i.name == 'email':
                i.attrs['readonly'] = 'true'
                break
    
def send_to_congress(p):
    from webapp import write_your_rep
    wyr = write_your_rep()
    return wyr.POST()   
        
class new:
    def GET(self):
        pform = forms.petitionform()
        fill_user_details(pform)
        return render.petitionform(pform)

    def POST(self):
        p = web.input()
        pform = forms.petitionform()
        auth.assert_verified(p.email)
        if pform.validates(p):
            if p.get('tocongress', 'off') == 'on': 
                sent_status = send_to_congress(p)
                if not isinstance(sent_status, bool):
                    return sent_status
                    
            save_petition(p)
            helpers.set_login_cookie(p.email)
            msg = """Congratulations, you've created your petition. 
                    Now sign and share it with all your friends."""
            helpers.set_msg(msg)
            return web.seeother('/%s' % p.pid)
        else:
            return render.petitionform(pform)
    
def askforpasswd(user_id):
    useremail = helpers.get_loggedin_email()
    #if the current user is the owner of the petition and has not set the password
    r = db.select('users', where='id=$user_id AND email=$useremail AND password is NULL', vars=locals())
    return bool(r)

def save_password(forminput):
    password = auth.encrypt_password(forminput.password)
    db.update('users', where='id=$forminput.user_id', password=password, vars=locals())
    helpers.set_msg('Password stored')

def save_signature(forminput, pid):        
    try:
        user = db.select('users', where='email=$forminput.email', vars=locals())[0]
    except:
        user_id = db.insert('users', lname=forminput.lname, fname=forminput.fname, email=forminput.email)
        user = web.storage(id=user_id, lname=forminput.lname, fname=forminput.fname, email=forminput.email)
        
    signed = db.select('signatory', where='petition_id=$pid AND user_id=$user.id', vars=locals())
    if not signed:
        signature = dict(petition_id=pid, user_id=user.id, 
                        share_with=forminput.share_with, comment=forminput.comment)
        db.insert('signatory', **signature)
        helpers.set_msg('Your signature has been taken for this petition.')
        helpers.unverified_login(user.email)
    return user    
               
def sendmail_to_signatory(user, pid):
    p = db.select('petition', where='id=$pid', vars=locals())[0]
    p.url = 'http//watchdog.net/c/%s' % (pid) 
    token = auth.get_secret_token(user.email)
    msg = render_plain.signatory_mailer(user, p, token)
    #@@@ shouldn't this web.utf8 stuff taken care by in web.py?
    web.sendmail(web.utf8(config.from_address), web.utf8(user.email), web.utf8(msg.subject.strip()), web.utf8(msg))
    
def is_author(email, pid):
    if not email: return False
     
    try:
        user_id = db.select('users', where='email=$email', what='id', vars=locals())[0].id
        owner_id = db.select('petition', where='id=$pid', what='owner_id', vars=locals())[0].owner_id
    except:
        return False
    else:
        return user_id == owner_id
                
class signatories:
    def GET(self, pid):
        user_email = helpers.get_loggedin_email()
        ptitle = db.select('petition', what='title', where='id=$pid', vars=locals())[0].title
        signs = db.select(['signatory', 'users'], 
                            what='users.fname, users.lname, users.email, '
                                 'signatory.share_with, signatory.comment',
                            where='petition_id=$pid AND user_id=users.id',
                            order='signtime desc',
                            vars=locals()).list()
        return render.signature_list(pid, ptitle, signs, is_author(user_email, pid))
                    
class petition:
    def GET(self, pid, signform=None, passwordform=None):
        i = web.input()
        
        options = ['unsign', 'edit', 'delete']
        if i.get('m', None) in options:
            handler = getattr(self, 'GET_'+i.m)
            return handler(pid)

        try:
            p = db.select('petition', where='id=$pid', vars=locals())[0]
        except:
            raise web.notfound
        
        p.signatory_count = db.query('select count(*) from signatory where petition_id=$pid',
                                        vars=locals())[0].count
        
        if not signform:
            signform = forms.signform()
            fill_user_details(signform, ['name', 'email'])
                                              
        if askforpasswd(p.owner_id) and not passwordform: passwordform = forms.passwordform()
        msg, msg_type = helpers.get_delete_msg()   
        return render.petition(p, signform, passwordform, msg)
    
    def GET_edit(self, pid):
        user_email = helpers.get_loggedin_email()
        if is_author(user_email, pid):
            p = db.select('petition', where='id=$pid', vars=locals())[0]
            pform = forms.petitionform()            
            pform.fill(email=user_email, pid=p.id, ptitle=p.title, msg=p.description)
            for i in pform.inputs:
                if i.id in ['pid', 'email']: i.attrs['readonly'] = 'true'
            title = "Edit petition"    
            return render.petitionform(pform, title, target='/c/%s?m=edit' % (pid))     
        else:
            login_link = '<a href="/login">Login</a>'
            helpers.set_msg('Only author of this petition can edit it. %s if you are.' % login_link, msg_type='error')
            raise web.seeother('/%s' % pid)
                    
    
    def GET_unsign(self, pid):
        i = web.input()
        user = helpers.get_user_by_email(i.email)
        
        if user:
            signatory = db.select('signatory', where='petition_id=$pid and user_id=$user.id', vars=locals())
        
        if not (user and signatory and auth.check_secret_token(i.email, i.token)):
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
            msg = render_plain.confirm_deletion(pid)
            helpers.set_msg(msg)
        else:
            login_link = '<a href="/login">Login</a>'
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
        form = forms.signform()
        i = web.input()
        if form.validates(i):
            user = save_signature(i, pid)
            sendmail_to_signatory(user, pid) 
            return web.seeother('/%s' % pid)
        else:
            return self.GET(pid, signform=form)
    
    def POST_edit(self, pid):
        i = web.input()
        db.update('petition', where='id=$pid', title=i.ptitle, description=i.msg, vars=locals())
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
    
def get_contacts(user_id):    
    contacts = db.select('contacts', 
                    what='cname as name, cemail as email, provider',
                    where='user_id=$user_id',
                    vars=locals()).list()
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

def not_signed(contact, pid):
    email = contact.email
    try:
        user_id = db.select('users', what='id', where='email=$email', vars=locals())[0].id
    except IndexError:
        return True
    else:
        is_signatory = db.select('signatory', where='user_id=$user_id and petition_id=$pid', vars=locals())
        return not bool(is_signatory)
    
class share:
    def GET(self, pid, emailform=None, loadcontactsform=None):
        i = web.input()
        user_id = helpers.get_loggedin_userid()
        contacts = get_contacts(user_id)
        contacts = filter(lambda c: not_signed(c, pid), contacts)
        petition = db.select('petition', where='id=$pid', vars=locals())[0]
        petition.url = 'http://watchdog.net/c/%s' %(pid)
        
        if not emailform: 
            emailform = forms.emailform
            subject='Share petition "%s"' % (petition.title)   
            msg = render_plain.share_petition_mail(petition)
            emailform.fill(subject=subject, body=msg)
            
        current_providers = set(c.provider.lower() for c in contacts)
        all_providers = set(['google', 'yahoo'])
        remaining_providers = all_providers.difference(current_providers)
        remaining_providers = ' or '.join(p.title() for p in remaining_providers)
        
        if remaining_providers and not loadcontactsform: 
            loadcontactsform = forms.loadcontactsform
        return render.share_petition(petition, emailform, 
                            contacts, remaining_providers, loadcontactsform)
        
    def POST(self):
        i = web.input()
        emailform = forms.emailform()
        if emailform.validates(i):
            pid, msg, subject = i.pid, i.body, i.subject
            emails = [e.strip() for e in i.emails.strip(', ').split(',')]
            web.sendmail(config.from_address, emails, subject, msg)
            helpers.set_msg('Thanks for sharing this petition with your friends!')    
            raise web.seeother('/%s' % (pid))
        else:
            return self.GET(emailform=emailform)    
        

app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
