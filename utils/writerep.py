#!/usr/bin/env python
# encoding: utf-8
"""
writerep.py
Write Your Representative
Created by Pradeep Gowda on 2008-04-24.
"""

from urllib2 import urlopen
from ClientForm import ParseFile, ParseError, ControlNotFoundError
from BeautifulSoup import BeautifulSoup
from StringIO import StringIO

import web
import captchasolver
from settings import db


PRODUCTION_MODE = False # XXX: read from config?
def production_click(form):
    if PRODUCTION_MODE:
        request = form.click()
        response = urlopen(request.get_full_url(), request.get_data())
    else:
        print 'Success',
        #print form
    return True

def has_message(soup,msg):
    bs = soup.findAll('b')
    msg = msg.lower()
    for b in bs:
        errmsg = str(b.string).lower()
        if errmsg.find(msg) > -1:
            return True
    return False

def has_captcha(soup):
    paras = soup.findAll('p')
    for p in paras:
        if p and p.string and p.string.find('spam') > -1:
            return True
    return False

def get_challenge(soup):
    labels =  filter(lambda x: x.get('for') == 'HIP_response', soup.findAll('label')) 
    if labels: return labels[0].string
    else: return None
    
def proc_forms(url, data=None):    
    response = urlopen(url, data).read()
    try:
        forms = ParseFile(StringIO(response), url, backwards_compat=False)
    except ParseError:
        forms = []
    return forms, response

def get_myform(request):
    url, data = request.get_full_url(), request.get_data() 
    forms, response = proc_forms(url, data)
    soup = BeautifulSoup(response)    
    if len(forms) < 2:
        if has_message(soup, "is shared by more than one"):
            #raise Exception("Zipcode is shared by more than one representative")
            print 'Zipcode is shared by more than one representative',
        elif has_message(soup, "not correct for the selected State"):
            #raise Exception("The Zip Code is not correct for the selected State.")
            print 'The Zip Code is not correct for the selected State.'
        elif has_message(soup, "was not found in our database."):
            #raise Exception("The Zip Code was not found in our database.")
            print 'The Zip Code was not found in our database'
        elif has_message(soup, "Use your web browser's <b>BACK</b> capability "):
            print 'Something wrong'
        elif forms:
            return forms[0]    
        else:
            print 'Error:', response
            return 
    elif has_captcha(soup):
        challenge = get_challenge(soup)
        form = forms[1]
        solution = captchasolver.solve(challenge)
        form['HIP_response'] = str(solution)
        request = form.click()
        form = get_myform(request)
        return form
    else:
        return forms[1]
        

def fill_name(form, prefix, fname, lname):    
    name = "%s %s %s" % (prefix, fname, lname)
    fill_field(form, 'pre', [prefix])
    return fill_field(form, 'lname', lname) and \
            fill_field(form, ['fname', 'name'], fname) or \
            fill_field(form, 'name', name)


def writerep_wyr(district, zipcode, state, prefix_name, first_name, last_name,
            addr1, city, phone, email, msg, addr2='', addr3='', zip4=''):
    """Note: Not all the wyr forms are same.
    """        
    def wyr_step1(url):
        forms, response = proc_forms(url)
        form = forms[1]
        # state names are in form: "PRPuerto Rico"
        state_options = form.find_control(name='state').items
        state_l = [s.name for s in state_options if s.name[:2] == state]
        status = fill_field(form, 'state', state_l) and \
                 fill_field(form, 'zip', zipcode) and \
                 fill_field(form, 'zip4', zip4)
        if status:
            print 'step1 done',
            request = form.click()
            return request
            
    def wyr_step2(request):
        if not request: return None
        form = get_myform(request)
        if form and fill_name(form, prefix_name, first_name, last_name):
            address = addr1 + addr2 + addr3
            fill_field(form, 'addr1', addr1) and \
            fill_field(form, 'addr2', addr2) or \
            fill_field(form, 'addr', address)

            fill_field(form, 'city', city)
            fill_field(form, 'phone', phone)
            fill_field(form, 'email', email)    
            request = form.click()
            print 'step2 done',
            return request
            

    def wyr_step3(request):
        if not request: return None
        form = get_myform(request)
        if form and fill_field(form, ['msg', 'message'], msg):
            print 'step3 done',
            return production_click(form)

    wyr_url = 'https://forms.house.gov/wyr/welcome.shtml'
    return wyr_step3(wyr_step2(wyr_step1(wyr_url)))

def is_ima_form(form):
    c = matching_control(form, ['message', 'msg'])
    return c and c.type == 'textarea'

def matching_control(form, names):
    '''return the form control matching given names'''
    names = [n.upper() for n in names]
    controls = [c for c in form.controls if c.name and not c.readonly]
    for s in names:
        for c in controls:
            if s in c.name.upper(): return c
            

def writerep_ima(ima_link, district, zipcode, state, prefix_name, first_name, 
                 last_name, addr1, city, phone, email, msg, 
                 addr2='', addr3='', zip4=''):

    forms, response = proc_forms(ima_link)
    if not forms: 
        print 'Error:', response
        return
    ima_forms = filter(is_ima_form, forms)[0]
    if isinstance(ima_forms, list): ima_form = ima_forms[0]
    else: ima_form = ima_forms

    #@@@ ima forms don't necessary have required-xxxx as their field names
    fill_field(ima_form, 'prefix', prefix_name)
    fill_field(ima_form, 'first', first_name)    
    fill_field(ima_form, 'last', last_name)
    fill_field(ima_form, 'address', '  '.join([addr1, addr2, addr3]))
    fill_field(ima_form, 'city', city)
    fill_field(ima_form, 'state', [state.upper()])
    fill_field(ima_form, 'zip5', zipcode)
    fill_field(ima_form, 'zip4', zip4)
    fill_field(ima_form, 'email', email)
    fill_field(ima_form, 'issue', ['GEN', 'OTH'])
    if fill_field(ima_form, ['message', 'msg'], msg):
        return production_click(ima_form)
    else:
        print 'Error:', response    
    
                     
def has_wyr_form(district):
    wyr_forms = db.select('wyr', what='wyr_form', 
                          where='district = $district and wyr_form IS NOT NULL', 
                          vars=locals())
    if wyr_forms: return True
    return False


def get_ima_link(district):
    contactforms = db.select('wyr', what='contactform', 
                             where='district = $district and imaissue = true', 
                             vars=locals())
    if contactforms: return contactforms[0].contactform
    return None


def get_zipauth_link(district):
    contactforms = db.select('wyr', what='contactform', 
                             where='district = $district and zipauth = true', 
                             vars=locals())
    if contactforms: return contactforms[0].contactform
    return None

def find_form(forms, names):
    names = [name.upper() for name in names]
    fform = None
    for form in forms:
        for c in form.controls:
            for name in names:
                if c.name and (name in c.name.upper()):
                    fform = form
    return fform

def select_value(control, mychoices):
    options = [str(item).lstrip('*') for item in control.items]
    for option in options:
        for mychoice in mychoices: 
            if mychoice.upper() in option.upper():
                return [option]
    return [option]            
            
def fill_field(form, names, value):
    """ fills the matching `form` field with `value`"""
    if not isinstance(names, list): names = [names]
    control = matching_control(form, names)
    if control:
        if control.type == 'select': value = select_value(control, value)
        form[control.name] = value
        return True    
    return False
    
def writerep_zipauth(zipauth_link, district, zipcode, state, prefix_name, first_name, 
                     last_name, addr1, city, phone, email, msg, 
                     addr2='', addr3='', zip4=''):
    forms, response = proc_forms(zipauth_link)
    form = find_form(forms, ['zip'])
    if form:
        fill_field(form, ['first', 'fname'], first_name)
        fill_field(form, ['last', 'lname'], last_name)
        fill_field(form, 'email', email)
        fill_field(form, 'zip', zipcode)
        fill_field(form, ['zip4', 'four','4'], zip4)
    else: 
        print 'Error:', response
        return

    request = form.click()
    forms, response = proc_forms(request.get_full_url(), request.get_data())
    form = find_form(forms, ['msg', 'message', 'topic', 'city','zip'])
    if form:
        fill_field(form, 'pre', [prefix_name])
        fill_field(form, ['first', 'name'], first_name)
        fill_field(form, ['last', 'name'], last_name)
        fill_field(form, ['addr1', 'addr'], addr1 + addr2 + addr3)
        fill_field(form, 'city', city)
        fill_field(form, ['zip', 'zipcode'], zipcode)
        fill_field(form, 'email', email)
        fill_field(form, 'phone', phone)
        fill_field(form, ['topic, subject'], ['GEN', 'OTH', 'OTHER'])
        fill_field(form, ['msg', 'message'], msg )
              
        return production_click(form)
    else:
        print 'Error:', response
    
def writerep(rep, zipcode, prefix_name, first_name, last_name, 
             addr1, city, phone, email, msg, addr2='', addr3='', zip4=''):
    '''
    Note: zip4 is required for contactforms with `zipauth` flag
    as well as those with multiple representatives for the district
    '''
    state, district, zipcodes = rep2state_dist_zips(rep)
    if not zipcode: zipcode = zipcodes[0]
    
    args = locals();
    args.pop('rep'); args.pop('zipcodes')
    
    wyr = has_wyr_form(district)
    ima_link = get_ima_link(district)
    zipauth_link = get_zipauth_link(district)
    msg_sent = False

    if wyr:
        print 'wyr_form',
        msg_sent = writerep_wyr(**args)

    if ima_link and not msg_sent:
        print 'ima_link',
        args['ima_link'] = ima_link
        msg_sent = writerep_ima(**args)
        
    if zipauth_link and not msg_sent:
        print 'zip auth',
        args['zipauth_link'] = zipauth_link
        msg_sent = writerep_zipauth(**args)
    
    return msg_sent

def rep2state_dist_zips(repname):
    repname = repname.replace(' ', '_')
    try:
        district = db.select('politician', what='district', where='id=$repname', vars=locals())[0].district
    except:
        return None
    else:
        zipcodes = getzips(district)
        state = district[:2]
        return state, district, zipcodes

def getdistzipdict(zipdump):
    """returns a dict with district names as keys zipcodes falling in it as values"""
    d = {}
    for line in zipdump.strip().split('\n'):
        zipcode, districts = line.split(': ', 1)
        districts = districts.split(' ')
        for dist in districts:
            d.setdefault(dist, []).append(zipcode)
    return d

try:        
   dist_zip_dict =  getdistzipdict(file('zipdict.txt').read())
except:
   import os, sys
   path = os.path.dirname(sys.modules[__name__].__file__)
   dist_zip_dict =  getdistzipdict(file(path + '/zipdict.txt').read())

def getzips(dist):
    return dist_zip_dict[dist]
        
def test(formtype=None):
    query = "select id from wyr, politician where politician.district=wyr.district " 
    if formtype == 'wyr':  query += "and wyr_form='t'"
    elif formtype == 'ima': query += "and imaissue='t'"
    elif formtype == 'zipauth': query += "and zipauth='t'"
    
    pols = (p.id for p in db.query(query))
    
    for pol in pols:
        print '\n', pol,        
        writerep(pol, zipcode='', prefix_name='Mr.', 
                 first_name='watchdog', last_name ='Tester', addr1='111 av', city='test city', 
                 phone='001-001-001', email='test@watchdog.net', msg='testing...')

    
if __name__ == '__main__':
    test('wyr')
