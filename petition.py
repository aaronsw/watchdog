
from __future__ import with_statement
import os
import hmac

import web
from utils import forms

urls = (
  '/c/', 'index',
  '/c/new/', 'new', 
  '/c/(.*)', 'petition'
)

render = web.template.render('templates/', base='base')
db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'),
                  db='watchdog_dev')
    
def secretkey():
    try:
        secret = file('.secret_key').read()
    except IOError:
       secret = os.urandom(20)
       file('.secret_key', 'w').write(secret)
    return secret

def _hmac(msg):
    return hmac.new(secretkey(), msg).hexdigest() 
       
def setcookie(name, value):
    encoded = value + '#@#' + _hmac(value)   
    web.setcookie(name, encoded)       
    
def getcookie(name):
    encoded = web.cookies().get(name, '#@#')
    value, hmac_value = encoded.split('#@#')
    if _hmac(value) == hmac_value:
        return value
    return None  

def deletecookie(name):
    web.setcookie(name, expires=-1)           
       
def set_msg(msg):       
    web.setcookie('wd_msg', msg)
    
def get_delete_msg():
    msg = web.cookies().get('wd_msg', None)
    web.setcookie('wd_msg', '', expires=-1)
    return msg
         
class index:
    def GET(self):
        petitions = db.select('petition', what='id, title',  order='created').list()
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
                setcookie('wd_email', p.email)
                
                set_msg("Congratulations, you've created your petition. Now share it with all your friends.")                        
                return web.seeother('/c/%s' % p.id)
        else:
            return render.petitionform(pform)
            
class petition:
    def GET(self, pid):
        try:
            p = db.select('petition', where='id=$pid', vars=locals())[0]
        except:
            raise web.notfound
        
        p.signatory_count = db.query('select count(*) from signatory where petition_id=$pid',
                                        vars=locals())[0].count
        signform = forms.signform()        
        msg = get_delete_msg()
        return render.petition(p, signform, msg=msg)
        
    def POST(self, pid):
        p = web.input()
        try:
            user_id = db.select('users', where='email=$p.email', vars=locals())[0].id
        except:
            user_id = db.insert('users', name=p.name, email=p.email)
            
        signed = db.select('signatory', where='petition_id=$pid AND user_id=$user_id', vars=locals())
        if not signed:
            db.insert('signatory', seqname=False, petition_id=pid, user_id=user_id)
            set_msg('Your signature has been taken for this petition.') 
                    
        setcookie('wd_email', p.email)    
        return web.seeother('/c/%s' % pid)
  
app = web.application(urls, globals())