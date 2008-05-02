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
from ClientForm import ParseFile
from BeautifulSoup import BeautifulSoup
import tempfile
import captchasolver

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

def writerep_wyr(zipcode, state, name, addr1, city, phone, email, msg, addr2='', addr3='', zip4=''):
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
    print form3
    ## XXX: uncomment only in production.
    ## request = form.click()
    ## response = urlopen(request.get_full_url(), request.get_data())
    ## XXX: Possibly check for "thank you" message for asserting successful dispatch of mail.

if __name__ == '__main__':
    # state='MA', zipcode='01773' #shared
    # state='PR', zipcode='00667', #success
    # state='MA', zipcode='01073', #captcha
    
    writerep_wyr(state='MA', zipcode='01532', name='watchdog test', addr1='111 av', city='test city',
            phone='001-001-001', email='test@watchdog.net', msg='testing...')
