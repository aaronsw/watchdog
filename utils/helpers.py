import os
import hmac
import web

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
