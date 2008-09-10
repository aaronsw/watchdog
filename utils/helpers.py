import os
import hmac

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
    return None

def deletecookie(name):
    web.setcookie(name, expires=-1)

def set_msg(msg, msg_type=None):
    if msg_type == 'error':
        msg += '$ERR$'
    web.setcookie('wd_msg', msg)

def get_delete_msg():
    msg = web.cookies().get('wd_msg', None)
    web.setcookie('wd_msg', '', expires=-1)

    msg_type = None
    if msg and msg.endswith('$ERR$'):
        msg_type = 'error'
        msg = msg[:-5]
    return msg, msg_type

def get_loggedin_email():
    return getcookie('wd_login')

def get_unverified_email():
    return getcookie('wd_email')

def get_loggedin_userid():
    email = get_loggedin_email()
    user = get_user_by_email(email)
    return user and user.id or None

def get_user_by_email(email):
    try:
        return db.select('users', where='email=$email', vars=locals())[0]
    except:
        return None

def set_login_cookie(email):
    setcookie('wd_login', email)

def del_login_cookie():
    web.setcookie("wd_login", "", expires=-1)

def unverified_login(email):
    setcookie('wd_email', email)

def no_verified_activity(email):
    verified = db.select('users', where='email=$email and verified=True', vars=locals())
    return not bool(verified)

def query_param(param, default_value):
    d = {param:default_value}
    i = web.input(**d)
    return i.get(param)

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
g['is_logged_in'] = lambda: bool(get_loggedin_email())

import markdown
g['format'] = markdown.markdown

import blog
g['blog_content'] = blog.content

import re
r_html = re.compile(r'<[^>]+?>')
def striphtml(x):
    return r_html.sub('', x).replace('\n', ' ')
g['striphtml'] = striphtml
