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
    print 'paras:', len(paras)
    for p in paras:
        print p.string
        if p:
            if p.string.find('spam') > -1:
                return True
    return False


def get_myform(url,data=None): 
    response = urlopen(url, data)
    tf = tempfile.mktemp()
    f = open(tf, 'w')
    f.write(response.read())
    response.close()
    f.close(); f = open(tf,'r')
    forms = ParseFile(f, url)
    f.close()
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
            raise Exception("Captcha found")

    else: return forms[1]

def writerep(**kw):
    state = kw.get('state').upper()
    zipcode = kw.get('zipcode')
    states = {}
 
    form = get_myform('https://forms.house.gov/wyr/welcome.shtml')

    # state names are in form: ``PRPuerto Rico"
    for item in form.find_control(name='state').items:
        states.update({item.name[:2]: item.name})
    
    form['state'] = [states[state]]
    form['zip'] = zipcode
    
    request = form.click()
    form2 = get_myform(request.get_full_url(), request.get_data())
    
    form2['name'] = kw.get('name')
    form2['addr1'] = kw.get('addr1')
    form2['addr2'] = kw.get('addr2')
    form2['addr3'] = kw.get('add3')
    form2['city'] = kw.get('city')
    form2['phone'] = kw.get('phone')
    form2['email'] = kw.get('email')

    form3 = get_myform(form.click())
    
    form3['msg'] = kw.get('msg')

    ## XXX: uncomment only in production.
    ## request = form.click()
    ## response = urlopen(request.get_full_url(), request.get_data())
    ## XXX: Possibly check for "thank you" message for asserting successful dispatch of mail.

if __name__ == '__main__':
    import sys
    if sys.argv[1:]:
        writerep(state=sys.argv[1], zipcode=sys.argv[2])
    else:
        writerep(state='MA', zipcode='02138')

