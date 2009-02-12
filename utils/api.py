import web
from wyrutils import getdist, dist2pols, has_captcha
import writerep, wyrapp, messages
from auth import new_user
import simplejson
from settings import db

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
INVALID_CAPTCHA_VALUE = 3, "Invalid captcha value"
NUM_ERR_CODES = 3

def get_pols(i):
    district = i.get('district', '')
    dist = getdist(i.get('zip5', ''), i.get('zip4', ''), i.get('address', ''))
    dist = dist and dist[0]
    if district and dist:
        if district != dist:
            raise WYR_Error(INVALID_ZIP_OR_ADDRESS)
    else:
        district = district or dist
    i['district'] = district    
    pols = dist2pols(district)
    if not pols:
        if i.get('district'):
            raise WYR_Error(INVALID_DISTRICT)
        else:
            raise WYR_Error(INVALID_ZIP_OR_ADDRESS)
    return pols

def validate(i):
    reqs = ['prefix', 'fname', 'lname', 'address', 'city', 'zip5', 'subject', 'msg']
    d = dict((r, r.title()) for r in reqs)
    d.update(fname='First Name', lname='Last Name', msg='Message')

    for r in reqs:
        if not i.get(r):
            err_code_msg = reqs.index(r)+NUM_ERR_CODES+1, 'Invalid %s' % d[r]
            raise WYR_Error(err_code_msg)

    if 'env' in i:
        env = simplejson.loads(i.env)
        for pol in env:
            if env[pol]['captcha_src'] and not env[pol].get('captcha_value'):
                raise WYR_Error(INVALID_CAPTCHA_VALUE)
            elif env[pol]['captcha_src']:
                i['captcha_%s' % pol] = env[pol]['captcha_value']

    return get_pols(i)
    
class wyr_prepare:
    def GET(self):
        i = web.input()
        pols = get_pols(i)
        e = {}
        for pol in pols:
    	    e[pol] = has_captcha(pol) and writerep.prepare(pol) or dict(captcha_src=None)
        return e

def get_userid():
    useremail = 'apiuser@opencongress.com' # change it later
    uid = db.select('users', where="email=$useremail", vars=locals())
    return uid and uid[0].id or new_user(useremail, 'apiuser').id

class wyr_send:
    def POST(self):
        i = web.input()
        pols = validate(i)
        uid = get_userid()
        i['ptitle'] = i.get('subject')
        i['addr1'], i['addr2'] = i.get('address'), ''
        i['state'] = i.district[:2]
        env = simplejson.loads(i.get('env', '{}'))
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
