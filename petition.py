
from __future__ import with_statement

import web
from utils import forms, helpers
from settings import db, render

urls = (
  '/c/', 'index',
  '/c/new/', 'new', 
  '/c/(.*)', 'petition'
)
        
class index:
    def GET(self):
        petitions = db.select('petition', what='id, title',  order='created desc').list()
        return render.petition_list(petitions)
        
class new:
    def GET(self):
        pform = forms.petitionform()
        return render.petitionform(pform)
         
    def POST(self):
        pform = forms.petitionform()
        if pform.validates(): 
            p = pform.d
            p.id = p.id.replace(' ', '_')
            with db.transaction():
                try:
                    owner_id = db.select('users', what='id', where='email=$p.email', vars=locals())[0].id
                except:
                    owner_id = db.insert('users', email=p.email) 
               
                db.insert('petition', seqname=False, id=p.id, title=p.title, description=p.description,
                            owner_id=owner_id)
                    
                #make the owner of the petition sign for it (??)                
                db.insert('signatory', seqname=False, user_id=owner_id, petition_id=p.id)
                helpers.setcookie('wd_email', p.email)
                helpers.set_msg("Congratulations, you've created your petition. Now share it with all your friends.")                        
                return web.seeother('/c/%s' % p.id)
        else:
            return render.petitionform(pform)
            
def askforpasswd(user_id):
    useremail = helpers.getcookie('wd_email')
    #if the current user is the owner of the petition and has not set the password
    r = db.select('users', where='id=$user_id AND email=$useremail AND password is NULL', vars=locals())
    return bool(r)

def insert_password(i):
    password = helpers.encrypt(i.password)
    db.update('users', where='id=$i.user_id', password=password, vars=locals())
    helpers.set_msg('Password stored')

def take_signature(i, pid):        
    try:
        user_id = db.select('users', where='email=$i.email', vars=locals())[0].id
    except:
        user_id = db.insert('users', name=i.name, email=i.email)

    signed = db.select('signatory', where='petition_id=$pid AND user_id=$user_id', vars=locals())
    if not signed:
        db.insert('signatory', seqname=False, petition_id=pid, user_id=user_id)
        helpers.set_msg('Your signature has been taken for this petition.')    
        helpers.setcookie('wd_email', i.email)
                
class petition:
    def GET(self, pid, signform=None, passwordform=None):
        try:
            p = db.select('petition', where='id=$pid', vars=locals())[0]
        except:
            raise web.notfound
        
        p.signatory_count = db.query('select count(*) from signatory where petition_id=$pid',
                                        vars=locals())[0].count
                                           
        signform = signform or forms.signform()
        if askforpasswd(p.owner_id) and not passwordform: passwordform = forms.passwordform()
        msg = helpers.get_delete_msg()
        
        return render.petition(p, signform, passwordform, msg)
        
    def POST(self, pid):
        i = web.input('m', _method='GET')
        if i.m == 'sign':
            return self.POST_sign(pid)
        elif i.m == 'password':
            return self.POST_password(pid)
        else:
            raise ValueError
    
    def POST_password(self, pid):
        form = forms.passwordform()
        i = web.input()
        if form.validates(i):
            insert_password(i)
            raise web.seeother('/c/%s' % pid)
        else:
            return self.GET(pid, passwordform=form)
            
    def POST_sign(self, pid):
        form = forms.signform()
        i = web.input()
        if form.validates(i):
            take_signature(i, pid)
            return web.seeother('/c/%s' % pid)
        else:
            return self.GET(pid, signform=form)
  
app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
