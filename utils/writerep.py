#!/usr/bin/env python
# encoding: utf-8
"""
writerep.py
Write Your Representative
Created by Pradeep Gowda on 2008-04-24.
"""

import sys
import os
from urllib2 import urlopen
from ClientForm import ParseFile, ControlNotFoundError
from BeautifulSoup import BeautifulSoup
import tempfile
import captchasolver
import web
import re


PRODUCTION_MODE = False # XXX: read from config?
def production_click(form):
    if PRODUCTION_MODE:
        request = form.click()
        response = urlopen(request.get_full_url(), request.get_data())
    else: print form

def has_message(soup,msg):
    bs = soup.findAll('b')
    msg = msg.lower()
    for b in bs:
        errmsg = b.string.lower()
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
    
def proc_forms(url,data=None):
    response = urlopen(url, data)
    tf = tempfile.mktemp()
    f = open(tf, 'w')
    f.write(response.read())
    response.close()
    f.close(); f = open(tf,'r')
    forms = ParseFile(f, url)
    f.close()
    return forms,tf
    
def get_myform(url,data=None): 
    forms, tf = proc_forms(url,data)
    soup = BeautifulSoup(open(tf, 'r').read())
    try:
        os.remove(tf)
    except OSError:
        pass
    if len(forms) < 2:
        if has_message(soup, "is shared by more than one"):
            raise Exception("Zipcode is shared by more than one representative")
        elif has_message(soup, "not correct for the selected State"):
            raise Exception("The Zip Code is not correct for the selected State.")
        elif has_message(soup, " was not found in our database."):
            raise Exception("The Zip Code was not found in our database.")
    elif has_captcha(soup):
        challenge = get_challenge(soup)
        form = forms[1]
        solution = captchasolver.solve(challenge)
        form['HIP_response'] = str(solution)
        request = form.click()
        form = get_myform(request.get_full_url(), request.get_data())
        return form
    else: return forms[1]

def writerep_wyr(district, zipcode, state, name, addr1, city, phone, email, msg, addr2='', addr3='', zip4=''):
    states = {} 
    forms,tf = proc_forms('https://forms.house.gov/wyr/welcome.shtml')
    form = forms[1]
    # state names are in form: ``PRPuerto Rico"
    for item in form.find_control(name='state').items:
        states.update({item.name[:2]: item.name})
    
    form['state'] = [states[state]]
    form['zip'] = zipcode
    form['zip4'] = zip4
    request = form.click()
    form2 = get_myform(request.get_full_url(), request.get_data())
        
    form2['name'] = name
    form2['addr1'] = addr1
    form2['addr2'] = addr2
    form2['addr3'] = addr3
    form2['city'] = city
    form2['phone'] = phone
    form2['email'] = email

    request = form2.click()
    form3 = get_myform(request.get_full_url(), request.get_data())
    form3['msg'] = msg
    production_click(form)
   

def is_ima_form(form):
    try:
        if form.find_control('required-message', type='textarea'):
            return True
    except ControlNotFoundError:
        pass
    return False


def matching_control(form, names):
    '''return the form control matching given names'''
    names = [n.upper() for n in names]
    for c in form.controls:
        for s in names:
            if s in c.name.upper(): return c
    return None


def writerep_ima(ima_link, district, zipcode, state, prefix_name, first_name, 
                 last_name, addr1, city, phone, email, msg, 
                 addr2='', addr3='', zip4=''):

    forms, tf = proc_forms(ima_link)
    states = {}
    ima_forms = filter(is_ima_form, forms)[0]
    if isinstance(ima_forms, list): ima_form = ima_forms[0]
    else: ima_form = ima_forms

    for i in ima_form.find_control('required-state').items:
        states.update({str(i): str(i)})
        
    ima_form['required-prefix']= prefix_name
    ima_form['required-first'] = first_name
    ima_form['required-last'] = last_name
    ima_form['required-address'] = '  '.join([addr1, addr2, addr3])
    ima_form['required-city'] = city
    state = state.upper()
    ima_form['required-state'] = [states.get(state)] or [states.get('*'+state)]
    ima_form['zip5'] = zipcode
    ima_form['zip4'] = zip4
    ima_form['required-email'] = email
    ima_form['required-issue'] = [matching_control(ima_form, ['GEN','OTH'])]
    ima_form['required-message'] = msg
    production_click(ima_form)
    

                     
def has_wyr_form(db, district):
    wyr_forms = db.select('wyr', what='wyr_form', 
                          where='district = $district and wyr_form IS NOT NULL', 
                          vars=locals())
    if wyr_forms: return True
    return False


def get_ima_link(db,district):
    contactforms = db.select('wyr', what='contactform', 
                             where='district = $district and imaissue = true', 
                             vars=locals())
    if contactforms: return contactforms[0].contactform
    return None


def get_zipauth_link(db,district):
    contactforms = db.select('wyr', what='contactform', 
                             where='district = $district and zipauth = true', 
                             vars=locals())
    if contactforms: return contactforms[0].contactform
    return None


def get_gen_issue(control, pref_names):
    for i in control.items:
        s = str(i).upper()
        if any([lambda x: x in s for x in pref_names]): return str(i)
    return str(i)


def find_form(forms, names):
    names = [name.upper() for name in names]
    fform = None
    for form in forms:
        for c in form.controls:
            for name in names:
                if name in c.name.upper():
                    fform = form
    return fform



def writerep_zipauth(zipauth_link, district, zipcode, state, prefix_name, first_name, 
                     last_name, addr1, city, phone, email, msg, 
                     addr2='', addr3='', zip4=''):
    print zipauth_link,
    print zipcode
    forms,tf = proc_forms(zipauth_link)
    print 'Zipauth Form:'
    form = find_form(forms, ['zip'])
    if form:
        zipc5 = matching_control(form, ['zip'])
        zipc4 = matching_control(form, ['zip4', 'four','4'])
        form[zipc5.name] = zipcode
        form[zipc4.name] = zip4
    else: return

    request = form.click()
    response = urlopen(request.get_full_url(), request.get_data())
    forms,tf =  proc_forms(response.url)
    print "Contact Form:"
    form = find_form(forms, ['msg', 'message', 'topic', 'city','zip'])
    if form:
        ffname = matching_control(form, ['required-name', 'first', 'name'])
        flname = matching_control(form, ['required-last', 'last', 'name'])
        faddr1 = matching_control(form, ['required-addr', 'addr1', 'addr'])
        fcity = matching_control(form, ['required-city','city'])
        fzip5 = matching_control(form, ['zip', 'zipcode'])
        femail = matching_control(form, ['required-email', 'email'])
        ftopic = matching_control(form, ['required-topic', 'topic', 'subject'])
        fmsg = matching_control(form, ['msg', 'message'])

        form[ffname.name] = first_name
        form[flname.name] = last_name
        if faddr1: form[faddr1.name] = addr1
        if fcity: form[fcity.name] = city
        if fzip5: form[fzip5.name] = zipcode
        if femail: form[femail.name] = email
        if ftopic: form[ftopic.name] =[get_gen_issue(ftopic, ['GEN', 'OTH', 'OTHER'])]
        if fmsg: form[fmsg.name] = fmsg
        production_click(form)

    
def writerep(db, district,zipcode, state, prefix_name, first_name, last_name, 
             addr1, city, phone, email, msg,  addr2='', addr3='', zip4=''):
    '''
    Note: zip4 is required for contactforms with `zipauth` flag
    as well as those with multiple representatives for the district
    '''

    args = locals(); args.pop('db')

    if has_wyr_form(db, district):
        names = [args.pop(n) for n in ['prefix_name', 'first_name', 'last_name']]
        name = ' '.join(names)
        args['name'] = name
        writerep_wyr(**args)

    ima_link = get_ima_link(db, district)
    if ima_link:
        args['ima_link'] = ima_link
        writerep_ima(**args)

    zipauth_link = get_zipauth_link(db, district)
    if zipauth_link:
        args['zipauth_link'] = zipauth_link
        writerep_zipauth(**args)


if __name__ == '__main__':
    # state='MA', zipcode='01773' #shared
    # state='PR', district='PR-01', zipcode='00667', #success
    # state='MA', zipcode='01073', #captcha
    # state='TX', district='TX-24' #no wyr_form
    # state='CA', district='CA-09', zipcode='94720',  #ima issue
    # state='FL', district='FL-03', zipcode='32206', #ima issue page with multiple forms
    # state='VA', district='VA-04', zipcode='23320', #zipauth
    # state='AR', district='AR-01', zipcode='72023', #generic contactform
    # state='OH', district='OH-01', zipcode='45202', #zipauth

    db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'), 
                      db='watchdog_dev')

    writerep(db=db, district='OH-01', state='OH', zipcode='45203', prefix_name='Mr.', 
             first_name='watchdog', last_name ='Tester', addr1='111 av', city='test city', 
             phone='001-001-001', email='test@watchdog.net', msg='testing...')
