import os
import hmac
import web
from config import secret_key
from . settings import db

def encrypt(msg, key=None):
    return hmac.new(key or secret_key, msg).hexdigest() 
       
def setcookie(name, value):
    encoded = value + '#@#' + encrypt(value)   
    web.setcookie(name, encoded)       
    
def getcookie(name):
    encoded = web.cookies().get(name, '#@#')
    value, encrypt_value = encoded.split('#@#')
    if encrypt(value) == encrypt_value:
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

def get_loggedin_email():
    return getcookie('wd_login') 

def get_unverified_email():
    return getcookie('wd_email')                

def get_loggedin_userid():
    email = get_loggedin_email()
    if email:
        return db.select('users', what='id', where='email=$email', vars=locals())[0].id
    else:
        return None    

def login(email):
    setcookie('wd_login', email)

def unverified_login(email):
    setcookie('wd_email', email)

def query_param(param, default_value):
    i = web.input()
    if param in i:
        return getattr(i, param)
    else:
        return default_value
