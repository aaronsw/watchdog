
from __future__ import with_statement

import web
from utils import forms, helpers, auth
from settings import db, render
import config

urls = (
  '', 'redir',
  '/', 'index',
  '/new', 'new', 
  '/checkID', 'checkID',
  '/share', 'share',
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
                    where='petition.id = signatory.petition_id',
                    group='petition.id, petition.title',
                    order='count(signatory.user_id) desc'
                    )
        return render.petition_list(petitions)
        
def save_petition(p):
    p.id = p.id.replace(' ', '_')
    with db.transaction():
        try:
            owner = db.select('users', where='email=$p.email', vars=locals())[0]
        except:
            owner_id = db.insert('users', email=p.email, verified=True) 
        else:
            if not owner.verified: db.update('users', where='email=$p.email', verified=True, vars=locals())
            owner_id = owner.id
            
        db.insert('petition', seqname=False, id=p.id, title=p.title, description=p.description,
                    owner_id=owner_id)
        #make the owner of the petition sign for it (??)             
        db.insert('signatory', seqname=False, user_id=owner_id, share_with='E', petition_id=p.id)      
        
def fill_user_details(form, fillings):
    details = {}
    if 'email' in fillings:
        email = helpers.get_loggedin_email() or helpers.get_unverified_email()
        if email: details['email'] = email

    if email and 'name' in fillings: 
        name = db.select('users', what='name', where='email=$email', vars=locals())[0].name
        if name: details['name'] = name
    
    form.fill(**details)
    
    if helpers.get_loggedin_email():
        for i in form.inputs:
            if i.name in details.keys():
                i.attrs['readonly'] = 'true'
        
class new:
    def GET(self):
        pform = forms.petitionform()
        fill_user_details(pform, 'email')
        return render.petitionform(pform)

    def POST(self):
        p = web.input()
        pform = forms.petitionform()
        auth.assert_verified(p.email)
        if pform.validates(p):
            save_petition(p)
            helpers.set_login_cookie(p.email)
            msg = """Congratulations, you've created your petition. 
                    Now sign and share it with all your friends."""
            helpers.set_msg(msg)
            return web.seeother('/%s' % p.id)
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
        user_id = db.insert('users', name=forminput.name, email=forminput.email)
    else:
        user_id = user.id
        if user.name != forminput.name:
            db.update('users', where='id=$user_id', name=forminput.name, vars=locals())    
        
    user = web.storage(id=user_id, name=forminput.name, email=forminput.email)
    signed = db.select('signatory', where='petition_id=$pid AND user_id=$user.id', vars=locals())
    if not signed:
        signature = dict(petition_id=pid, user_id=user_id, 
                        share_with=forminput.share_with, comment=forminput.comment)
        db.insert('signatory', seqname=False, **signature)
        helpers.set_msg('Your signature has been taken for this petition.')
        helpers.unverified_login(user.email)
    return user    
               
def sendmail_to_signatory(user, pid):
    p = db.select('petition', where='id=$pid', vars=locals())[0]
    p.url = 'http//watchdog.net/c/%s' % (pid) 
    msg = render_plain.signatory_mailer(user.name, p)
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
                
class petition:
    def GET(self, pid, signform=None, passwordform=None):
        i = web.input()
        if ('m' in i):
            if i.m == 'edit':  return self.GET_edit(pid)
            elif i.m == 'signatories': return self.GET_signatories(pid)
        
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
        msg = helpers.get_delete_msg()   
        return render.petition(p, signform, passwordform, msg)
    
    def GET_edit(self, pid):
        user_email = helpers.get_loggedin_email()
        if is_author(user_email, pid):
            p = db.select('petition', where='id=$pid', vars=locals())[0]
            p.email = user_email
            pform = forms.petitionform()            
            pform.fill(**p)
            for i in pform.inputs:
                if i.id in ['id', 'email']: i.attrs['readonly'] = 'true'
            title = "Edit petition"    
            return render.petitionform(pform, title, target='/c/%s?m=edit' % (pid))     
        else:
            helpers.set_msg('Only author of this petition can edit it.')
            raise web.seeother('/%s' % pid)
            
    def GET_signatories(self, pid):
        user_email = helpers.get_loggedin_email()
        ptitle = db.select('petition', what='title', where='id=$pid', vars=locals())[0].title
        signs = db.select(['signatory', 'users'], 
                        what='users.name, users.email, '
                             'signatory.share_with, signatory.comment',
                        where='petition_id=$pid AND user_id=users.id',
                        order='signtime desc',
                        vars=locals()).list()
        return render.signature_list(pid, ptitle, signs, is_author(user_email, pid))
            
        
    def POST(self, pid):
        i = web.input('m', _method='GET')
        options = ['sign', 'unisign', 'edit', 'password']
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
            #@@@ no need of this anymore, as we have sharing through imported contacts
            #sendmail_to_signatory(user, pid) 
            return web.seeother('/%s' % pid)
        else:
            return self.GET(pid, signform=form)
    
    def POST_edit(self, pid):
        i = web.input()
        db.update('petition', where='id=$pid', title=i.title, description=i.description, vars=locals())
        raise web.seeother('/%s' % (pid))
    
    def POST_unsign(self, pid):
        pass #@@@for now                               
    
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
    
class share:
    def GET(self, emailform=None, loadcontactsform=None):
        i = web.input()
        user_id = helpers.get_loggedin_userid()
        contacts = get_contacts(user_id)
        petition = db.select('petition', where='id=$i.pid', vars=locals())[0]
        petition.url = 'http://watchdog.net/c/%s' %(i.pid)
        
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
