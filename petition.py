
from __future__ import with_statement

import web
import markdown
from utils import forms, helpers
from settings import db, render
import config

urls = (
  '', 'redir',
  '/', 'index',
  '/new', 'new', 
  '/checkID', 'checkID',
  '/(.*)', 'petition'
)

web.template.Template.globals['format'] = markdown.markdown

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
            owner_id = db.select('users', what='id', where='email=$p.email', vars=locals())[0].id
        except:
            owner_id = db.insert('users', email=p.email) 

        db.insert('petition', seqname=False, id=p.id, title=p.title, description=p.description,
                    owner_id=owner_id)
        #make the owner of the petition sign for it (??)  NO. better take name, comments also from sign form.              
        #db.insert('signatory', seqname=False, user_id=owner_id, petition_id=p.id)      
        
def fill_user_details(form, fillings):
    details = {}
    if 'email' in fillings:
        email = helpers.get_loggedin_email() or helpers.get_unverified_email()
        details['email'] = email

    if email and 'name' in fillings: 
        name = db.select('users', what='name', where='email=$email', vars=locals())[0].name
        details['name'] = name    
    
    form.fill(**details)
    
    if helpers.get_loggedin_email():
        for i in form.inputs:
            if i.name in fillings:
                i.attrs['readonly'] = 'true'
        
class new:
    def GET(self):
        pform = forms.petitionform()
        fill_user_details(pform, 'email')
        return render.petitionform(pform)
         
    def POST(self):
        pform = forms.petitionform()
        if pform.validates(): 
            p = pform.d
            save_petition(p)
            helpers.login(p.email)
            signurl = '<a href="#sign">sign</a>'
            msg = """Congratulations, you've created your petition. 
                    Now %s and share it with all your friends.""" %(signurl)
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
    password = helpers.encrypt(forminput.password)
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
                        email_privacy=forminput.email_privacy, comment=forminput.comment)
        db.insert('signatory', seqname=False, **signature)
        helpers.set_msg('Your signature has been taken for this petition.')
        helpers.unverified_login(user.email)
    return user    
               
def sendmail_to_signatory(user, pid):
    p = db.select('petition', where='id=$pid', vars=locals())[0]
    p.url = 'http//watchdog.net/c/%s' % (pid)
    render_plain = web.template.render('templates/') 
    msg = render_plain.signatory_mailer(user.name, p)
    #@@@ shouldn't this web.utf8 stuff taken care by in web.py?
    web.sendmail(web.utf8(config.from_address), web.utf8(user.email), web.utf8(msg.subject.strip()), web.utf8(msg))
    
def is_owner(email, pid):    
    try:
        user_id = db.select('users', where='email=$email', what='id', vars=locals())[0].id
        owner_id = db.select('petition', where='id=$pid', what='owner_id', vars=locals())[0].owner_id
        print user_id, owner_id
    except:
        return False
    else:
        return user_id == owner_id
                
class petition:
    def GET(self, pid, signform=None, passwordform=None):
        i = web.input()
        if ('m' in i) and (i.m == 'edit'):  return self.GET_edit(pid)

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
        if is_owner(user_email, pid):
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
            sendmail_to_signatory(user, pid)
            return web.seeother('/%s' % pid)
        else:
            return self.GET(pid, signform=form)
    
    def POST_edit(self, pid):
        i = web.input()
        db.update('petition', where='id=$pid', title=i.title, description=i.description, vars=locals())
        raise web.seeother('/%s' % (pid))
    
    def POST_unsign(self, pid):
        pass #@@@for now                               
        
        
app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
