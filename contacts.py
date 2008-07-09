import time
import md5
import urllib, urllib2 
from xml.dom import minidom    
from BeautifulSoup import BeautifulSoup
import string
import demjson

import web
from settings import db, render, session
from utils import helpers, forms

def yahooLoginURL(email, url, token=None):
    email = urllib.quote(email)
    lines = open('/home/watchdog/certs/yauth', 'r').readlines()
    appid = lines[0].rstrip()
    secret = lines[1].rstrip()
    ts = time.time()
    appdata = email
    yurl = 'https://api.login.yahoo.com'
    purl = '%s?appid=%s&appdata=%s&ts=%s' % (url,appid, appdata, ts)
    surl ='%s%s' % (purl, secret)
    sig = md5.new(surl).hexdigest()
    furl = '%s%s&sig=%s' % (yurl, purl, sig)
    if token: furl = '%s&token=%s' % ( furl, token)
    return  furl

def gmailLoginURL(email):
    url = 'https://www.google.com/accounts/AuthSubRequest?'
    scope = urllib2.quote('http://www.google.com/m8/feeds/')
    next = urllib2.quote('http://watchdog.net/authsub')
    url += 'scope='+scope+'&session=1&secure=0&next='+ next
    return url

class importcontacts:

    def GET(self):
        msg = helpers.get_delete_msg()
        return render.import_contacts(msg)

    def POST(self):
        i = web.input()
        email = i.get('email')
        form = forms.loadcontactsform()
        if form.validates(i):
            session.email = email
            session.pid = i.pid
            if i.provider == 'Yahoo':
                ylogin_url = yahooLoginURL(email, '/WSLogin/V1/wslogin')
                raise web.seeother(ylogin_url)
            elif i.provider == 'Google': 
                glogin_url = gmailLoginURL(email)
                raise web.seeother(glogin_url)
        else:
            import petition
            share_obj = petition.share()
            return share_obj.GET(form)
            
def save_contacts(email, contacts, provider):
    user_id = helpers.get_loggedin_userid()
    for c in contacts:
        cname, cemail = c['name'], c['email']
        vars = dict(user_id=user_id, uemail=email, cemail=cemail,
                    cname=cname, provider=provider)
        e = db.select('contacts', 
                    where='user_id=$user_id and uemail=$uemail and cemail=$cemail',
                    vars=vars)
        if not e: n = db.insert('contacts', seqname=False, **vars)
        else: db.update('contacts', cname=cname,
                    where='user_id=$user_id and uemail=$uemail and cemail=$cemail',
                    vars=vars)

class bbauth:
    def get_contacts(self, contacts_json):
        content = demjson.decode(contacts_json)
        
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
        appdata = i.get('appdata')        
        userhash = i.get('userhash')        
        ts = i.get('ts')        
        token = i.get('token')        
        email = session.email        
        #XXX: security verification etc..         
        url = yahooLoginURL(email, '/WSLogin/V1/wspwtoken_login', token)
        resp = urllib2.urlopen(url)        
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
        raise web.seeother('/c/share?pid=%s' % (session.pid))

class authsub:
    def get_contacts(self, contacts_feed):
        ATOM_NS = 'http://www.w3.org/2005/Atom'
        doc = minidom.parse(contacts_feed)
        entries = doc.getElementsByTagNameNS(ATOM_NS, u'entry')
        
        def get_text(elem):
            text = ''
            for node in elem.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    text += node.data
            return text
                    
        contacts = []
        for e in entries:
            e_title = e.getElementsByTagNameNS(ATOM_NS, u'title')[0]
            name = get_text(e_title)
            email = e.getElementsByTagName('gd:email')[0].getAttribute('address')
            contacts.append(dict(name=name, email=email))
        return contacts    

    def GET(self):
        i = web.input()
        authToken = i.get('token')
        email = session.email
        emailq = urllib2.quote(email)
        url = ("http://www.google.com/m8/feeds/contacts/%s/full?max-results=999" % emailq)
        headers = { 'Authorization' : 'AuthSub token="%s"' % authToken.strip() }
        request = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(request)
        contacts = self.get_contacts(response)
        save_contacts(email, contacts, provider='GOOGLE')
        raise web.seeother('/c/share?pid=%s' % (session.pid))
    
class yauth:
    def GET(self):
        return """
Phrase: "# and nation nation moved yet so ship or onwhether so now conceived any the that"
File: "ydnlIEWXo.html"
Url to Check: "http://watchdog.net/ydnlIEWXo.html"
"""
