import time
import md5
import urllib, urllib2 
from xml.etree import ElementTree as ET
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
        session.email = email
        session.pid = i.pid
        if 'yahoo' in email:
            ylogin_url = yahooLoginURL(email, '/WSLogin/V1/wslogin')
            web.seeother(ylogin_url)

        elif 'gmail' in email or 'googlemail' in email: 
            glogin_url = gmailLoginURL(email)
            web.seeother(glogin_url)
        else:
            return render.import_contacts(message='Not a valid email address. Please try again')


class bbauth:
    def save_contacts(self,email, contacts):
        for c in contacts:
            fields = c['fields']
            cemail = fields[0]['data']
            cfname = ' '; clname = ' '

            if len(fields) > 1:
                cfname = fields[1].get('first', ' ')
                clname = fields[1].get('last', ' ')

            cname = u'%s %s' % (cfname, clname)
            cname = cname.replace('&#39;', ' ').strip()
            vars = {'uemail': email, 'cemail': cemail,
                    'cname': cname, 'provider': 'YAHOO'}
            e = db.select('contacts', where='uemail=$uemail and cemail=$cemail',
                          vars=vars)
            if not e: n = db.insert('contacts', seqname=False, **vars)
            else: db.update('contacts', where='uemail=$uemail and cemail=$cemail',
                            vars=vars, cname=cname)


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
        resp = urllib2.urlopen(req).read()
        content = demjson.decode(resp)
        contacts = content.get('contacts')
        if contacts:
            self.save_contacts(email, contacts)
        raise web.seeother('/c/share?pid=%s' % (session.pid))

class authsub:
    def save_contacts(self, uemail,contacts):
        for cemail in contacts:
            cname = ''
            vars = {'uemail': uemail, 'cemail': cemail,
                    'cname':cname, 'provider': 'GMAIL'}
            e = db.select('contacts', where='uemail=$uemail and cemail=$cemail', 
                          vars=vars)
            if not e: n = db.insert('contacts', seqname=False, **vars)
            else: db.update('contacts', where='uemail=$uemail and cemail=$cemail',
                      vars=vars, cname=cname)

    def GET(self):
        i = web.input()
        authToken = i.get('token')
        email = session.email
        emailq = urllib2.quote(email)
        url = ("http://www.google.com/m8/feeds/contacts/%s/full?max-results=999" % emailq)
        headers = { 'Authorization' : 'AuthSub token="%s"' % authToken.strip() }
        request = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(request)
        tree = ET.XML(response.read())
        items = tree.getiterator()
        contacts = []
        for e in items:
            for i in e:
                #XXX: extract names
                address = i.attrib.get('address')
                if address: contacts.append(address)
        
        self.save_contacts(email, contacts)
        raise web.seeother('/c/share?pid=%s' % (session.pid))
    
class yauth:
    def GET(self):
        return """
Phrase: "# and nation nation moved yet so ship or onwhether so now conceived any the that"
File: "ydnlIEWXo.html"
Url to Check: "http://watchdog.net/ydnlIEWXo.html"
"""
