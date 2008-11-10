import os
import hmac
import base64

import web
from config import secret_key
from settings import db

def encrypt(msg, key=None):
    return hmac.new(key or secret_key, msg).hexdigest()

def setcookie(name, value, expires=''):
    encoded = value + '#@#' + encrypt(value)
    web.setcookie(name, encoded, expires)

def getcookie(name):
    encoded = web.cookies().get(name, '#@#')
    value, encrypt_value = encoded.split('#@#')
    if encrypt(value) == encrypt_value:
        return value

def deletecookie(name):
    web.setcookie(name, expires=-1)

def get_trackid(uid, pid):
    if not uid: return
    uid = str(uid)
    uid_pid = base64.urlsafe_b64encode(uid+pid[:10])
    return ':'.join([uid, uid_pid])

def check_trackid(tid, pid):
    try:
        uid, uid_pid = tid.split(':')
        uid_pid = base64.urlsafe_b64decode(str(uid_pid))
    except:
        return
    if uid_pid == uid + pid[:10]:
        return uid

def set_msg(msg, msg_type=None):
    if msg_type == 'error':
        msg += '$ERR$'
    elif msg_type == 'note':
        msg += '$NOTE$'    
    web.setcookie('wd_msg', msg)

def get_delete_msg():
    msg = web.cookies().get('wd_msg', None)
    web.setcookie('wd_msg', '', expires=-1)

    msg_type = None
    if msg:
        if msg.endswith('$ERR$'):
            msg_type = 'error'
            msg = msg[:-5]
        elif msg.endswith('$NOTE$'):
            msg_type = 'note'    
            msg = msg[:-6]
    return msg, msg_type

def get_loggedin_email():
    return getcookie('wd_login')

def get_unverified_email():
    return getcookie('wd_email')

def get_loggedin_userid():
    email = get_loggedin_email()
    user = get_user_by_email(email)
    return user and user.id
    
def get_unverified_userid():
    email = get_unverified_email()
    user = get_user_by_email(email)
    return user and user.id

def get_user_by_email(email):
    try:
        return db.select('users', where='email=$email', vars=locals())[0]
    except IndexError:
        return None

def set_login_cookie(email):
    setcookie('wd_login', email)

def del_login_cookie():
    web.setcookie("wd_login", "", expires=-1)

def del_unverified_cookie():
    web.setcookie("wd_email", "", expires=-1)
    
def unverified_login(email, fname, lname):
    setcookie('wd_email', email)
    if not get_user_by_email(email):
        db.insert('users', fname=fname, lname=lname, email=email)

def is_verified(email):
    verified = db.select('users', where='email=$email and (verified=True or password is not null)', vars=locals())
    return bool(verified)

def query_param(param, default_value):
    d = {param:default_value}
    i = web.input(**d)
    return i.get(param)

def get_user_name():
    email = get_loggedin_email() or get_unverified_email()
    user = get_user_by_email(email)
    return (user.fname or email[:email.index('@')]) if user else ''

g = web.template.Template.globals
g['slice'] = slice
g['commify'] = web.commify
g['int'] = int
g['abs'] = abs
g['len'] = len
g['changequery'] = web.changequery
g['enumerate'] = enumerate
g['datestr'] = web.datestr

g['query_param'] = query_param
g['is_logged_in'] = lambda: bool(get_loggedin_email() or get_unverified_email())

import markdown
g['format'] = markdown.markdown

import blog
g['blog_content'] = blog.content

import re
r_html = re.compile(r'<[^>]+?>')
def striphtml(x):
    return r_html.sub('', x).replace('\n', ' ')
g['striphtml'] = striphtml
g['getpath'] = lambda : web.ctx.homepath + web.ctx.path
g['cookies_on'] = lambda : bool(web.cookies().get('webpy_session_id'))
g['get_user_id'] = lambda: get_loggedin_userid() or get_unverified_userid()
g['get_user_name'] = get_user_name
