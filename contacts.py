import time, hashlib, urllib, urllib2, string
from xml.dom import minidom    
import simplejson as json
from BeautifulSoup import BeautifulSoup

import web
from settings import db, render
from utils import helpers, forms

def yahooLoginURL(email, url, token=None, share_url='/', title=''):
    email = urllib.quote(email)
    lines = open('/home/watchdog/certs/yauth', 'r').readlines()
    appid = lines[0].rstrip()
    secret = lines[1].rstrip()
    ts = time.time()
    appdata = '|'.join([email, share_url, title])
    yurl = 'https://api.login.yahoo.com'
    purl = '%s?appid=%s&appdata=%s&ts=%s' % (url, appid, appdata, ts)
    surl ='%s%s' % (purl, secret)
    sig = hashlib.md5(surl).hexdigest()
    furl = '%s%s&sig=%s' % (yurl, purl, sig)
    if token: furl = '%s&token=%s' % ( furl, token)
    return  furl

def gmailLoginURL(email, share_url='/', title=''):
    gurl = 'https://www.google.com/accounts/AuthSubRequest?'
    scope = urllib2.quote('http://www.google.com/m8/feeds/')
    next = urllib2.quote(web.ctx.homedomain + '/authsub?email=%s&url=%s&title=%s' %(email, share_url, title))
    gurl += 'scope='+scope+'&session=1&secure=0&next='+ next
    return gurl
    
def msnLoginURL(email, share_url='/', title=''):
    murl = "https://consent.live.com/Delegation.aspx?RU=%s&ps=%s&pl=%s"
    appdata = '|'.join([email, share_url, title])
    return_url = urllib.quote(web.ctx.homedomain + '/auth/msn?appdata=%s' % appdata)
    permissions = 'Contacts.View'
    privacy_policy = urllib.quote(web.ctx.homedomain + '/privacy')
    murl = murl % (return_url, permissions, privacy_policy)
    #token = "appid=%s&ts=%s" % (getAppId(), time.time())
    #murl = murl + urllib.quote(token)
    return murl
    
class importcontacts:
    def GET(self):
        msg, msg_type = helpers.get_delete_msg()
        return render.import_contacts(msg)

    def POST(self):
        i = web.input()
        email, url, title = i.get('email', ''), i.get('url', '/'), i.get('title', '')
        form = forms.loadcontactsform()
        if form.validates(i):
            if i.provider == 'yahoo':
                ylogin_url = yahooLoginURL(email, '/WSLogin/V1/wslogin', share_url=url, title=title)
                raise web.seeother(ylogin_url)
            elif i.provider == 'google':
                glogin_url = gmailLoginURL(email, url, title)
                raise web.seeother(glogin_url)
            elif i.provider == 'msn':
                mlogin_url = msnLoginURL(email, url, title)
                raise web.seeother(mlogin_url)
        else:
            import petition
            share_obj = petition.share()
            emailform = forms.emailform()
            return share_obj.GET(emailform, form)
            
def save_contacts(email, contacts, provider):
    #Even if the user is not logged-in, but has an account with us, let him import contacts
    user_id = helpers.get_loggedin_userid()
    if not user_id:
        user = db.select('users', what='id', where='email=$email', vars=locals())
        if user: user_id = user[0].id
        
    if user_id:    
        for c in contacts:
            cname, cemail = c['name'], c['email']
            vars = dict(user_id=user_id, uemail=email, cemail=cemail,
                        cname=cname, provider=provider)
            e = db.select('contacts', 
                        where='user_id=$user_id and uemail=$uemail and cemail=$cemail',
                        vars=vars)
            if not e: n = db.insert('contacts', seqname=False, **vars)
            elif cname: db.update('contacts', cname=cname,
                        where='user_id=$user_id and uemail=$uemail and cemail=$cemail',
                        vars=vars)

class auth_yahoo:
    def get_contacts(self, contacts_json):
        content = json.loads(contacts_json)
        
        contacts = []
        for c in content.get('contacts'):
            fields = c['fields']
            cemail = fields[0]['data']
            cfname = ' '; clname = ' '

            if len(fields) > 1:
                cfname = fields[1].get('first', ' ')
                clname = fields[1].get('last', ' ')
        
            cname = u'%s %s' % (cfname, clname)
            cname = cname.replace('&#39;', ' ').strip()
            contacts.append(dict(email=cemail, name=cname))
        return contacts

    def GET(self):
        i = web.input()
        appid = i.get('appid').rstrip()
        email, url, title = i.get('appdata', '||').split('|')
        userhash = i.get('userhash')        
        ts = i.get('ts')        
        token = i.get('token')        
        query = urllib.urlencode(dict(url=url, title=title))
        if not token:
            raise web.seeother('/share?%s' % query)
        #XXX: security verification etc..
        url = yahooLoginURL(email, '/WSLogin/V1/wspwtoken_login', token)
        try:
            resp = urllib2.urlopen(url)
        except:
            helpers.set_msg('Authorization Failed.')
            raise web.seeother('/share?%s' % query)

        content = resp.read()
        soup = BeautifulSoup(content)        
        aurl = 'http://address.yahooapis.com/v1/searchContacts?format=json'
        wssid = soup.findAll('wssid')[0].contents[0]        
        cookie =soup.findAll('cookie')[0].contents[0]        
        cookie = cookie.strip()        

        furl = aurl + '&fields=email,name&email.present=1&appid=%s&WSSID=%s' % (appid, wssid)
        req = urllib2.Request(furl)
        req.add_header('Cookie', cookie)
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req).read()
        contacts = self.get_contacts(response)
        save_contacts(email, contacts, provider='YAHOO')
        raise web.seeother('/share?%s' % query)

def get_text(elem):
    #gets the text from XML DOM element `elem`
    text = ''
    for node in elem.childNodes:
        if node.nodeType == node.TEXT_NODE:
            text += node.data
    return text

class auth_google:
    def get_contacts(self, contacts_feed):
        ATOM_NS = 'http://www.w3.org/2005/Atom'
        doc = minidom.parse(contacts_feed)
        entries = doc.getElementsByTagNameNS(ATOM_NS, u'entry')
                    
        contacts = []
        for e in entries:
            e_title = e.getElementsByTagNameNS(ATOM_NS, u'title')[0]
            name = get_text(e_title)
            email = e.getElementsByTagName('gd:email')[0].getAttribute('address')
            contacts.append(dict(name=name, email=email))
        return contacts    

    def GET(self):
        i = web.input()
        query = urllib.urlencode(dict(url=i.get('url'), title=i.get('title')))
        authToken = i.get('token')
        if not authToken:
            raise web.seeother('/share?%s' % query)
        email = i.get('email')
        emailq = urllib2.quote(email, '')
        url = ("http://www.google.com/m8/feeds/contacts/%s/full?max-results=999" % emailq)
        headers = { 'Authorization' : 'AuthSub token="%s"' % authToken.strip() }
        request = urllib2.Request(url, None, headers)
        try:
            response = urllib2.urlopen(request)
        except:
            helpers.set_msg('Authorization Failed.')
        else:        
            contacts = self.get_contacts(response)
            save_contacts(email, contacts, provider='GOOGLE')
        raise web.seeother('/share?%s' % query)
        
class auth_msn:
    def get_consent(self, s):
        d = {}
        s = urllib.unquote(s)
        ts = s.split('&')
        for t in ts:
            k, v = t.split('=')
            d[k] = v
        return d

    def get_contacts(self, contacts_xml):
        contacts = []
        xmldoc = minidom.parse(contacts_xml)
        for c in xmldoc.getElementsByTagName('Contact'):
            name_elem = c.getElementsByTagName('SortName')[0]
            name = get_text(name_elem)
            email_elem = c.getElementsByTagName('Address')[0]
            email = get_text(email_elem)
            contacts.append(dict(name=name, email=email))
        return contacts

    def POST(self):
        i = web.input()
        appdata = i.get('appdata', '||')
        email, share_url, title = appdata.split('|')
        if i.get('ResponseCode', '') == 'RequestApproved':
            consent = self.get_consent(i.ConsentToken)
            lid = consent.get('lid')
            delegatedToken = urllib.unquote(consent.get('delt'))
            url = 'https://livecontacts.services.live.com'
            url += '/users/@L@' + lid + '/rest/LiveContacts/Contacts'
            request = urllib2.Request(url)
            request.add_header('Content-Type', 'application/xml; charset=utf-8')
            request.add_header('Authorization', 'DelegatedToken dt="%s"' % delegatedToken)
            try:
                response = urllib2.urlopen(request)
            except:
                helpers.set_msg('Authorization Failed.')
            else:        
                contacts = self.get_contacts(response)
                save_contacts(email, contacts, provider='MICROSOFT')

        query = urllib.urlencode(dict(url=share_url, title=title))
        raise web.seeother('/share?%s' % query)
