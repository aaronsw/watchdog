import web
from wyrutils import getdist, dist2pols, has_captcha
import writerep, wyrapp, messages
from auth import new_user
import simplejson

urls = (
    '/wyr\.prepare', 'wyr_prepare',
    '/wyr\.send', 'wyr_send',
    '/wyr\.getresponses', 'wyr_getresponses'
)

def api_processor(handler):
    try:
        result = handler()
    except WYR_Error, e:
        result = dict(err_code=e.code, err_msg=e.msg)

    web.header('Content-Type', 'application/json')    
    return simplejson.dumps(result)

class WYR_Error(Exception):
    def __init__(self, code_msg):
        code, msg = code_msg
        Exception.__init__(self, msg)
        self.code = code
        self.msg = msg
    
INVALID_DISTRICT = 1, "Invalid district"
INVALID_ZIP_OR_ADDRESS = 2, "Invalid zip and/or address"

def get_pols(i):
    district = i.get('district', '')
    district = district or getdist(i.get('zip5', ''), i.get('zip4', ''), i.get('address', ''))
    pols = dist2pols(district)
    if not pols:
        if i.get('district'):
            raise WYR_Error(INVALID_DISTRICT)
        else:
            raise WYR_Error(INVALID_ZIP_OR_ADDRESS)
    return pols

def validate(i):
    reqs = ['prefix', 'fname', 'lname', 'address', 'city', 'zip5', 'zip4', 'subject', 'msg']
    d = dict((r, r.title()) for r in reqs)
    d.update(fname='First Name', lname='Last Name', msg='Message')
    for r in reqs:
        if not i.get(r):
            raise WYR_Error(INVALID_ + d[r])
    return get_pols(i)

def compose(d):
    """make a dict just with captcha_url and state"""
    ret = {}
    for pol, env in d.iteritems():
        if env:
            ret[pol] = dict(captcha_src=env['captcha_src'], 
                            captcha_env=dict(cookies=env['cookies'],
                                            form=env['form']))
        else:    
            ret[pol] = dict(captcha_src=None)
            
    return ret        
    
class wyr_prepare:
    def GET(self):
        i = web.input()
        pols = get_pols(i)
        e = {}  
        for pol in pols:
        	e[pol] = has_captcha(pol) and writerep.prepare(pol)
        ret = compose(e)	
        return ret

def get_userid():
    useremail = 'apiuser@opencongress.com' # change it later
    uid = db.select('users', where="email=$useremail", vars=locals())
    return uid or new_user(useremail, 'apiuser').id
    
class wyr_send:
    def POST(self):
        i = web.input()
        d = simplejson.loads(i)
        pols = get_pols(d)
        uid = get_userid()
        env = {} # get it from input
        msgids = writerep.send_msgs(uid, i, source_id='wyr', pols=pols, env=env)
        ret = {}
        for pol in msgids:
            ret[pol] = dict(msgid=msgids[pol], status='SENT')
        return ret
        
class wyr_getresponses:
    def GET(self):
        i = web.input()
        msgid = i.get('msgid')
        responses = messages.get_responses(msgid)
        ret = []
        for r in responses:
            ret.append(dict(id=r.id, msgid=r.msgid, response=r.response, timestamp=r.received))        
        return ret

app = web.application(urls, globals())
app.add_processor(api_processor)

if __name__ == "__main__":
    app.run()
