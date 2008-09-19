#!/usr/bin/env python
# encoding: utf-8
"""
writerep.py
Write Your Representative
Created by Pradeep Gowda on 2008-04-24.
"""
import sys
import urllib2
from ClientForm import ParseFile, ParseError, ControlNotFoundError, AmbiguityError
from BeautifulSoup import BeautifulSoup
from StringIO import StringIO
import re
from urlparse import urljoin

import web
import captchasolver, forms, helpers, zip2rep
from settings import db, render
import petition

PRODUCTION_MODE = False
TEST_MODE = (not PRODUCTION_MODE) and True
TEST_EMAIL = 'test@watchdog.net'

name_options = dict(prefix=['pre', 'salutation'],
                    lname=['lname', 'last'],
                    fname=['fname', 'first', 'name'],
                    zipcode=['zip', 'zipcode'],
                    zip4=['zip4', 'four', 'plus'],
                    address=['addr1', 'address1', 'add1', 'address'],
                    addr2=['addr2', 'add2', 'address2'],
                    addr3=['addr3'],
                    city=['city'],
                    state=['state'],
                    email=['email'],
                    phone=['phone'],
                    issue=['issue', 'subject', 'topic', 'title'],
                    message=['message', 'msg', 'comment', 'text'],
                    captcha=['captcha', 'validat']
                )

def safe(f):
    def g(*args, **kw):
        try:
            return f(*args, **kw)
        except:
            print >> sys.stderr, '%s Failed with %s, %s' % (f.__name__, args, kw)
            return None
    return g        

@safe
def urlopen(url, data=None):
    return urllib2.urlopen(url, data)
    
def first(seq):
    """returns first True element"""    
    if not seq: return False
    for s in seq:
        if s:
            return s
    return None        

class Form(object):
    def __init__(self, f):
        self.f = f
        
    def __repr__(self):
        return repr(self.f)
        
    def __str__(self):
        return str(self.f)
                    
    def  __getattr__(self, x): 
        return getattr(self.f, x)
                        
    def production_click(self):
        if PRODUCTION_MODE:
            request = self.f.click()
            response = urlopen(request.get_full_url(), request.get_data())
        elif TEST_MODE:
            self.f.action = web.ctx.homedomain + '/wyrtest'
            request = self.f.click() 
            response = urlopen(request.get_full_url(), request.get_data())
            
        return True
    
    def click(self):
        try:
            return self.f.click()
        except Exception, detail:
            print >> sys.stderr, detail
                    
    def select_value(self, control, options):
        if not isinstance(options, list): options = [options]
        items = [str(item).lstrip('*') for item in control.items]
        for option in options: 
            for item in items:
                if option.lower() in item.lower():
                    return [item]
        return [item]

    def fill_all(self, **d):
        for k, v in d.items():
            self.fill(v, name=k)
                    
    def fill_name(self, prefix, fname, lname):
        self.fill(prefix, 'prefix')
        if self.fill(lname, 'lname'):
            return self.fill(fname, 'fname')
        else:
            name = "%s %s %s" % (prefix, lname, fname)
            return self.fill(fname, 'fname')
    
    def fill_address(self, addr1, addr2, addr3=''):    
        if self.fill(addr2, 'addr2'):
            return self.fill(addr1, 'address')
        else:
            address = "%s %s %s" % (addr1, addr2, addr3)
            return self.fill(address, 'address')

    def fill(self, value, name=None, type=None):
        c = self.find_control(name=name, type=type)
        if c and not c.readonly:
            if c.type in ['select', 'radio', 'checkbox']: 
                value = self.select_value(c, value)
            elif isinstance(value, list):
                value = value[0]
            self.f.set_value(value, name=c.name, type=c.type)
            return True 
        return False
    
    def has(self, name=None, type=None):
        return bool(self.find_control(name=name, type=type))
    
    def find_control(self, name=None, type=None):
        """return the form control of type `type` or matching name_options of `name`"""
        if not (name or type): return
        
        try:
            names = name_options[name]
        except KeyError: 
            names = name and [name]
        c = None
        if type: c = self.find_control_by_type(type)
        if not c and names: c = first(self.find_control_by_name(name) for name in names)
        if not c and names: c = first(self.find_control_by_id(name) for name in names)
        
        return c     

    def find_control_by_name(self, name):
        name = name.lower()
        return first(c for c in self.f.controls if c.name and name in c.name.lower())
        
    def find_control_by_id(self, id):
        id = id.lower()
        return first(c for c in self.f.controls if c.id and id in c.id.lower())
        
    def find_control_by_type(self, type):
        try:
            return self.f.find_control(type=type)
        except ControlNotFoundError:
            return None
        except AmbiguityError:  #@@  TO BE FIXED
            return self.f.find_control(type=type, nr=1)
            
            
def has_message(soup, msg, tags='b'):
    bs = soup.findAll(tags)
    msg = msg.lower()
    for b in bs:
        errmsg = str(b.string).lower()
        errmsg += ' '.join(str(c) for c in b.contents)
        if (errmsg.find(msg) > -1):
            return True
    return False

def get_forms(url, data=None):    
    response = urlopen(url, data)
    if response: response = response.read()
    try:
        forms = ParseFile(StringIO(response), url, backwards_compat=False)
    except:
        forms = []

    return [Form(f) for f in forms], response or ''

class ZipShared(Exception): pass
class ZipIncorrect(Exception): pass
class ZipNotFound(Exception): pass
class WyrError(Exception): pass
class NoForm(Exception): pass

def writerep_email(rep_email, district, zipcode, state, prefix, fname, lname,
            addr1, city, phone, email, subject, msg, addr2='', addr3='', zip4=''):
            
    name = '%s. %s %s' % (prefix, fname, lname)
    from_addr = '%s <%s>' % (name, email)
  
    if PRODUCTION_MODE:
        to_addr = rep_email.lstrip('mailto:')
    elif TEST_MODE:
        to_addr = TEST_EMAIL
    #@@@@ msg has to be composed    
    web.sendmail(from_addr, to_addr, subject, msg)
    return True        

def writerep_wyr(wyr_link, district, zipcode, state, prefix, fname, lname,
            addr1, city, phone, email, subject, msg, addr2='', addr3='', zip4=''):
          
    def wyr_step1(url):
        forms, response = get_forms(url)
        form = forms[1]
        # state names are in form: "PRPuerto Rico"
        state_options = form.find_control_by_name('state').items
        state_l = [s.name for s in state_options if s.name[:2] == state]
        form.fill_all(state=state_l[0], zip=zipcode, zip4=zip4)
        print 'step1 done',
        request = form.click()
        return request
            
    def get_challenge(soup):
          labels =  filter(lambda x: x.get('for') == 'HIP_response', soup.findAll('label')) 
          if labels: return labels[0].string
          else: return None        
            
    def get_wyr_form2(request):
        if not request: return
        url, data = request.get_full_url(), request.get_data() 
        forms, response = get_forms(url, data)
        soup = BeautifulSoup(response)    
        if len(forms) < 2:
            if has_message(soup, "is shared by more than one"): raise ZipShared
            elif has_message(soup, "not correct for the selected State"): raise ZipIncorrect
            elif has_message(soup, "was not found in our database."): raise ZipNotFound
            elif has_message(soup, "Use your web browser's <b>BACK</b> capability "): raise WyrError
            elif forms and 'search' not in forms[0].action.lower(): return forms[0]  
            else: raise NoForm
        else:
            challenge = get_challenge(soup)
            if challenge:
                form = forms[1]
                try:
                    solution = captchasolver.solve(challenge)
                except Exception, detail:
                    print >> sys.stderr, 'Exception in CaptchaSolve', detail
                    print 'Could not solve:"%s"' % challenge,
                else:        
                    form.f['HIP_response'] = str(solution)
                    request = form.click()
                    form = get_wyr_form2(request)
                    return form
            else:
                return forms[1]
        
    def wyr_step2(request):
        if not request: return
        form = get_wyr_form2(request)
        if not form: return

        if form.fill_name(prefix, fname, lname):
            form.fill_address(addr1, addr2, addr3)
            form.fill_all(city=city, phone=phone, email=email)
            request = form.click()
            print 'step2 done',
            return request
            
    def wyr_step3(request):
        if not request: return
        forms, response = get_forms(request.get_full_url(), request.get_data())
        forms = filter(lambda f: f.has(type='textarea'), forms)
        if forms:
            form = forms[0]
            if form.fill(msg, type='textarea'):
                print 'step3 done',
                return form.production_click()
        else:
            print >> sys.stderr, response

    return wyr_step3(wyr_step2(wyr_step1(wyr_link)))

def writerep_ima(ima_link, district, zipcode, state, prefix, fname, 
                 lname, addr1, city, phone, email, subject, msg, 
                 addr2='', addr3='', zip4='', captcha=''):

    forms, response = get_forms(ima_link)
    forms = filter(lambda f: f.has(type='textarea') , forms)
    
    if forms:
        f = forms[0]
        f.fill_name(prefix, fname, lname)
        f.fill_address(addr1, addr2, addr3)
        f.fill_all(city=city, state=state.upper(), zipcode=zipcode, zip4=zip4, email=email, phone=phone, issue=['GEN', 'OTH'])
        f.fill(type='textarea', value=msg)
        f.fill_all(captcha=captcha)
        return f.production_click()
    else:
        print 'Error: No IMA form in', ima_link,

def writerep_zipauth(zipauth_link, district, zipcode, state, prefix, fname, 
                     lname, addr1, city, phone, email, subject, msg, 
                     addr2='', addr3='', zip4=''):
            
    def zipauth_step1(f):    
        f.fill_name(prefix, fname, lname)
        f.fill_all(email=email, zipcode=zipcode, zip4=zip4)
        print 'step1 done',
        return f.click()
        
    def zipauth_step2(request):   
        if not request: return
        forms, response = get_forms(request.get_full_url(), request.get_data())
        forms = filter(lambda f: f.has(type='textarea'), forms)
        if forms:
            f = forms[0]
            f.fill_name(prefix, fname, lname)
            f.fill_address(addr1, addr2, addr3)
            f.fill_all(city=city, zip=zipcode, email=email, phone=phone, issue=['GEN', 'OTH'])
            f.fill(type='textarea', value=msg)
            print 'step2 done',
            return f.production_click()
        else:
            soup = BeautifulSoup(response)
            if has_message(soup, 'zip code is split between more', 'p'): raise ZipShared
            if has_message(soup, 'Access to the requested form is denied', ['p', 'font']): raise ZipIncorrect
            if has_message(soup, 'you are outside', 'p'): raise ZipIncorrect 
            
    forms, response = get_forms(zipauth_link)
    forms = filter(lambda f: f.has(name='zip'), forms)
    if forms:
        return zipauth_step2(zipauth_step1(forms[0]))
    else: 
        print 'Error: No zipauth form in', zipauth_link
        return        
    
def getcontact(dist):
    r = db.select('rep_contacts', what='contact, contacttype', where='district=$dist', vars=locals())
    if r: 
        r = r[0]                
        return r.contact, r.contacttype
    else:
        return None, None    
        
def writerep(district, zipcode, prefix, fname, lname, 
             addr1, city, phone, email, subject, msg, addr2='', addr3='', zip4='', captcha=''):
    '''
    Note: zip4 is required for contactforms with `zipauth` flag
    as well as those with multiple representatives for the district
    '''
    state = district[:2]
    prefix = prefix.rstrip('.') #few forms take only Mr, Ms etc.
    
    href, contacttype = getcontact(district)
    if contacttype not in ['E', 'W', 'I', 'Z']: return False
    args = locals();
    
    d = dict(E='rep_email', W='wyr_link', I='ima_link', Z='zipauth_link')
    args[d[contacttype]] = href
    args.pop('href'); args.pop('contacttype')
    if contacttype != 'I': args.pop('captcha')
         
    handlers = dict(E=writerep_email, W=writerep_wyr, I=writerep_ima, Z=writerep_zipauth)
    print handlers[contacttype].__name__,
    msg_sent = handlers[contacttype](**args)    
    return msg_sent
    
def get_captcha_src(dist):
    r = db.select('rep_contacts', what='contact', where="district=$dist and contacttype='I'", vars=locals())
    if r:
        url = r[0].contact
        response = urlopen(url)
        if response: 
            soup = BeautifulSoup(response)
            imgs = soup.findAll('img', attrs={'src': re.compile('.*[Cc]aptcha.*')})
            if imgs: 
                img_src = imgs[0].get('src', '') 
                return urljoin(url, img_src)
    return ''

def add_captcha(form, img_src):
    inputs = list(form.inputs)
    captcha = forms.captcha
    captcha.pre = '<img src="%s" border="0" />&nbsp;&nbsp;' % img_src
    inputs.append(captcha)
    form.inputs = tuple(inputs)
    return form

def get_wyrform(i, dist=None):
    form = forms.wyrform()    
    if (not dist) and form.validates(i):
         dist = zip2rep.getdists(i.zipcode, i.zip4, i.addr1+i.addr2)[0]
    captcha = forms.captcha     
    captcha_needed = ('captcha' in i) and not captcha.validate(i.captcha, form)
    captcha_src = captcha_needed and get_captcha_src(dist)
    if captcha_src:
        add_captcha(form, captcha_src)  
    return form  

     
class write_your_rep:
    def __init__(self):
        self.msg_id = None
        self.dist = None

    def set_dist(self, i):
        try:
            self.dist = zip2rep.getdists(i.zipcode, i.zip4, i.addr1+i.addr2)[0]
        except KeyError:
            raise ZipIncorrect
            
    def set_msg_id(self, msg_id, petition=False):
        #set msg id to trace the responses
        #msg_id should let's know whether msg is sent through petition signatures or /writerep
        #set msg_id to odd if msg is from signatures, even if msg is from /writerep
        msg_id = 2 * msg_id
        if petition: msg_id += 1
        self.msg_id = web.to36(msg_id)
                
    def save_msg(self, subj, msg):
        uemail = helpers.get_loggedin_email()
        user = helpers.get_user_by_email(uemail)
        user_id = user and user.id
        msg_id = db.insert('wyr', district=self.dist, subject=subj, message=msg, sender=user_id, sent=False)
        return msg_id

    def send_msg(self, i, wyrform, pform=None):
        dist = self.dist
        captcha_src = ('captcha' not in i) and get_captcha_src(dist)
        if captcha_src:
            wyrform = add_captcha(wyrform, captcha_src)
            if pform:
                return render.petitionform(pform, wyrform)
            else:
                return render.writerep(wyrform)

        email = 'p-%s@watchdog.net' % (self.msg_id)
        msg_sent = writerep(district=dist,
                        prefix=i.prefix, lname=i.lname, fname=i.fname,
                        addr1=i.addr1, addr2=i.addr2, city=i.city,
                        zipcode=i.zipcode, zip4=i.zip4,
                        phone=i.phone, email=email, subject=i.ptitle, msg=i.msg,
                        captcha=i.get('captcha', ''))
        return msg_sent

    def save_and_send_msg(self, i, wyrform, pform=None):
        self.set_dist(i)
        msg_id = self.save_msg(i.ptitle, i.msg)     
        self.set_msg_id(msg_id)
        msg_sent = self.send_msg(i, wyrform, pform)
        if msg_sent == True:
            db.update('wyr', where='id=$msg_id', sent=True, vars=locals())
        return msg_sent    
    
    def GET(self, form=None):
        if not form:
            form = forms.wyrform()
            petition.fill_user_details(form)
        msg, msg_type = helpers.get_delete_msg()
        return render.writerep(form, msg=msg)

    def POST(self):
        i = web.input()
        wyrform = get_wyrform(i)
        if wyrform.validates(i):
            status = self.save_and_send_msg(i, wyrform)
            if not isinstance(status, bool):
                return status
            if status: helpers.set_msg('Your message has been sent.')
            raise web.seeother('/writerep')
        else:
            return self.GET(wyrform)

def get_from_input(key, input=None):
       if not input: input = web.input()
       possibles = name_options[key]
       for name in possibles:
           for k in input.keys():
               if name in k.lower():
                   return input.get(k)

class wyr_test:
    def POST(self):
        i = web.input()
        to_addr = TEST_EMAIL
        from_addr = get_from_input('email', i) or ''
        subject = get_from_input('issue', i) or ''
        msg = get_from_input('message', i) or ''
        web.sendmail(from_addr, to_addr, subject, msg)
        return 

def test(formtype=None):
    def getdistzipdict(zipdump):
        """returns a dict with district names as keys zipcodes falling in it as values"""
        d = {}
        for line in zipdump.strip().split('\n'):
            zip5, zip4, dist = line.split('\t')
            d[dist] = (zip5, zip4)
        return d

    try:        
       dist_zip_dict =  getdistzipdict(file('zip_per_dist.tsv').read())
    except:
       import os, sys
       path = os.path.dirname(sys.modules[__name__].__file__)
       dist_zip_dict =  getdistzipdict(file(path + '/zip_per_dist.tsv').read())

    def getzip(dist):
        return dist_zip_dict[dist]
          
    query = "select district from rep_contacts " 
    if formtype == 'wyr':  query += "where contacttype='W'"
    elif formtype == 'ima': query += "where contacttype='I'"
    elif formtype == 'zipauth': query += "where contacttype='Z'"
    elif formtype =='email': query += "where contacttype='E'"
    
    dists = [r.district for r in db.query(query + ' limit 2')]
    for dist in dists:
        print dist,        
        zip5, zip4 = getzip(dist)
        msg_sent = writerep(dist, zipcode=zip5, zip4=zip4, prefix='Mr.', 
                    fname='watchdog', lname ='Tester', addr1='111 av', addr2='addr extn', city='test city', 
                    phone='001-001-001', email='test@watchdog.net', subject='general', msg='testing...')
        print msg_sent and 'Success' or 'Failure'
    
if __name__ == '__main__':
    #test('email')
    test('wyr')
    #test('ima')
    #test('zipauth')
