import web
from zip2rep import zip2dist
from settings import db

import sys
import urllib2
from ClientForm import ControlNotFoundError, AmbiguityError
from BeautifulSoup import BeautifulSoup
import re
from urlparse import urljoin


class ZipShared(Exception): pass
class ZipIncorrect(Exception): pass
class ZipNotFound(Exception): pass
class WyrError(Exception): pass
class NoForm(Exception): pass
class CaptchaException(Exception): pass


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

def numdists(zip5, zip4=None, address=None):
    return len(getdists(zip5, zip4, address))

def getdists(zip5, zip4=None, address=None):
    query = 'select distinct district_id from zip4 where zip=$zip5'
    if zip4: query += ' and plus4=$zip4'
    query += ' limit 2'     #just to see uniqness of districts
    dists = [x.district_id for x in db.query(query, vars=locals())]
    if len(dists) != 1:
        try:
            dists = zip2dist(zip5, address and address.strip())
        except Exception, details:
            pass
    return dists

def has_captcha(pol):
    r = db.select('pol_contacts', what='contact', where="politician_id=$pol and captcha='t'", vars=locals())
    return bool(r)
        
def get_captcha_src(pol):
    if has_captcha(pol):
        r = db.select('pol_contacts', what='contact', where="politician_id=$pol", vars=locals())
        url = r[0].contact
        response = urlopen(url)
        if response: 
            soup = BeautifulSoup(response)
            imgs = soup.findAll('img', attrs={'src': re.compile('.*[Cc]aptcha.*')})
            if imgs: 
                img_src = imgs[0].get('src', '') 
                return urljoin(url, img_src)

def add_captcha(wf):
    try:
        dist = getdists(wf.zipcode.value, wf.zip4.value, wf.addr1.value+wf.addr2.value)[0]
    except:
        pass
    else:        
        src = get_captcha_src(dist2pol(dist))
        set_captcha(wf, src)

def set_captcha(wyrform, img_src):
    if img_src:
        wyrform.captcha.pre = '<img src="%s" border="0" />&nbsp;&nbsp;' % img_src

def pol2dist(pol):
    try:
        return db.select('politician', what='district_id', where='politician.id=$pol', vars=locals())[0].district_id
    except KeyError:
        return

def dist2pol(dist):
    try:
        return db.select('politician', what='id', where='politician.district_id=$dist', vars=locals())[0].id
    except KeyError:
        return

def urlopen(*args):
    try:
        return urllib2.urlopen(*args)    
    except Exception, details:
        print details,
        if isinstance(args[0], urllib2.Request): print args[0].get_full_url(),
        else: print args[0],

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
        from writerep import production_mode, test_mode
        if production_mode:
            request = self.f.click()
            response = urlopen(request.get_full_url(), request.get_data())
        elif test_mode:
            home = web.ctx.get('homedomain') or 'http://0.0.0.0:8080'
            self.f.action = home + '/writerep/test'
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

    def fill_phone(self, phone):
        phone = phone + ' '* (10 - len(phone)) # make phone length 10
        ph_ctrls = [c.name for c in self.f.controls if not c.readonly and c.name and 'phone' in c.name.lower()]
        num_ph = len(ph_ctrls)
        if num_ph == 1:
            return self.f.set_value(phone, ph_ctrls[0], nr=0)
        elif num_ph == 2:
            self.f.set_value(phone[:3], name=ph_ctrls[0], nr=0)
            self.f.set_value(phone[3:], name=ph_ctrls[1], nr=0)
        elif num_ph == 3:
            self.f.set_value(phone[:3], name=ph_ctrls[0], nr=0)
            self.f.set_value(phone[3:6], name=ph_ctrls[1], nr=0)
            self.f.set_value(phone[6:], name=ph_ctrls[2], nr=0)

    def fill(self, value, name=None, type=None):
        c = self.find_control(name=name, type=type)
        if c and not c.readonly:
            if c.type in ['select', 'radio', 'checkbox']: 
                value = self.select_value(c, value)
            elif isinstance(value, list):
                value = value[0]
            self.f.set_value(value, name=c.name, type=c.type, nr=0)
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

