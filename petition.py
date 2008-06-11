
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
                
class petition:
    def GET(self, pid, form=None):
        try:
            p = db.select('petition', where='id=$pid', vars=locals())[0]
        except:
            raise web.notfound
        
        p.signatory_count = db.query('select count(*) from signatory where petition_id=$pid',
                                        vars=locals())[0].count
                                           
        signform = form or forms.signform()       
        msg = helpers.get_delete_msg()
        passwordform = askforpasswd(p.owner_id) and forms.passwordform() or None
        
        return render.petition(p, signform, passwordform, msg)
        
    def POST(self, pid):
        signform = forms.signform()   
        if signform.validates():
            i = web.input()
            try:
                user_id = db.select('users', where='email=$i.email', vars=locals())[0].id
            except:
                user_id = db.insert('users', name=i.name, email=i.email)
            
            signed = db.select('signatory', where='petition_id=$pid AND user_id=$user_id', vars=locals())
            if not signed:
                db.insert('signatory', seqname=False, petition_id=pid, user_id=user_id)
                helpers.set_msg('Your signature has been taken for this petition.') 
                    
            helpers.setcookie('wd_email', i.email)    
            return web.seeother('/c/%s' % pid)
        else:
            return self.GET(pid, signform)
            
  
app = web.application(urls, globals())
