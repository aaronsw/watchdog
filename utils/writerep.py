"""
Functions to send msgs to reps and deal with captchas
"""

import sys
from BeautifulSoup import BeautifulSoup
from ClientForm import ParseFile, ParseError, XHTMLCompatibleFormParser
from StringIO import StringIO
import re, urllib2
from urlparse import urljoin

import web
from settings import db
from wyrutils import *
from utils import captchasolver, messages, helpers

__all__ = ["prepare", "send_msgs", "send", "writerep"]

def prepare(pol):
    """
    Checks if the `pol`'s contact url has captcha, and if so - takes care of
    with cookies, return env with captcha url and form having captcha.
    """
    env = {}
    url = getcontact(pol).get('contact')
    response = urlopen(url)
    captcha_src, form = get_img_and_form(response)
    if captcha_src:
	    env['captcha_src'], env['form'] = captcha_src, form
    return env

def send(frm, to, subj, msg, user_details, source_id=None, env={}):
    """
    Sends the given `msg` to `to`, with the `user_details` and saves it in DB. 
    uses `env` if `to` has captcha.
    """
    msgid = messages.save_msg(frm, to, subj, msg, source_id)
    user_details.email = 'p-%s@watchdog.net' % web.to36(msgid)
    user_details.full_msg = compose_msg(to, msg)
    user_details.subject = user_details.ptitle
    status = writerep(to, user_details, env)
    if status: messages.update_msg_status(msgid, status)

def send_msgs(uid, i, source_id, pols=[], env={}):
    """
    Sends msgs to ALL the politcians who are senators/reps of the 
    district defined by zip5, zip4, address in i
    """
    pols = pols or getpols(i.zip5,  i.zip4, i.addr1+i.addr2)
    for pol in pols:
	    send(uid, pol, i.ptitle, i.msg, i, source_id, env.get(pol, {}))

def compose_msg(polid, msg):
    #@@ compose msg here
    p = db.select('politician', where='id=$polid', 
            what='firstname, middlename, lastname, district_id', vars=locals())[0]
    pol_name = "%s %s %s" % (p.firstname or '', p.middlename or '', p.lastname or '') 
    rep_or_sen = 'Sen.' if len(p.district_id) == 2 else 'Rep.'
    full_msg = 'Dear %s %s,\n%s' % (rep_or_sen, pol_name, msg)
    return full_msg

def writerep(pol, i, env={}):
    """
    Checks for the contact type for the `pol` and calls one of writerep_{wyr, ima, email} 
    with the contact url appropriately and returns the status.
    """
    i.prefix = i.get('prefix', '.').rstrip('.') #few forms take only Mr, Ms etc.
    c = getcontact(pol)
    if not c: return False
    contact, contacttype = c.contact, c.contacttype
    handlers = dict(E=writerep_email, W=writerep_wyr, I=writerep_ima, Z=writerep_zipauth)
    try:
        handler = handlers[contacttype]
        if contacttype == 'I':
            msg_sent = handler(pol, contact, i, env)
        else:
            msg_sent = handler(pol, contact, i)    
    except Exception, details:
        print >> sys.stderr, 'Error in writerep:', details
        msg_sent = False
    return msg_sent

def writerep_email(pol, pol_email, i):
    name = '%s. %s %s' % (i.prefix, i.fname, i.lname)
    from_addr = '%s <%s>' % (name, i.email)
  
    if production_mode:
        to_addr = web.lstrips(pol_email, 'mailto:')
    elif test_mode:
        to_addr = test_email
    web.sendmail(from_addr, to_addr, subject, msg)
    return True

def writerep_wyr(pol, wyr_link, i):
    """Sends the msg along with the sender details from `i` through the WYR system.
    The WYR system has 3 forms typically (and a captcha form for few reps in between 1st and 2nd forms).
    Form 1 asks for state and zipcode
    Form 2 asks for sender's details such as prefix, name, city, address, email, phone etc
    Form 3 asks for the msg to send.
    """
    def wyr_step1(url):
        forms, response = get_forms(url)
        form = forms[0]
        # state names are in form: "PRPuerto Rico"
        state_options = form.find_control_by_name('state').items
        state_l = [s.name for s in state_options if s.name[:2] == i.state]
        form.fill_all(state=state_l[0], zipcode=i.zip5, zip4=i.zip4)
        print 'step1 done',
        request = form.click()
        return request
            
    def get_challenge(soup):
          labels =  filter(lambda x: x.get('for') == 'HIP_response', soup.findAll('label')) 
          if labels: return labels[0].string
            
    def get_wyr_form2(request):
        if not request: return
        url, data = request.get_full_url(), request.get_data() 
        forms, response = get_forms(url, data)
        soup = BeautifulSoup(response)
        if len(forms) < 1:
            if has_message(soup, "is shared by more than one"): raise ZipShared
            elif has_message(soup, "not correct for the selected State"): raise ZipIncorrect
            elif has_message(soup, "was not found in our database."): raise ZipNotFound
            elif has_message(soup, "Use your web browser's <b>BACK</b> capability "): raise WyrError
            else: raise NoForm
        else:
            challenge = get_challenge(soup)
            if challenge:
                form = forms[0]
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
                return forms[0]
        
    def wyr_step2(request):
        if not request: return
        form = get_wyr_form2(request)
        if not form: return

        if form.fill_name(i.prefix, i.fname, i.lname):
            form.fill_address(i.addr1, i.addr2)
            form.fill_all(city=i.city, phone=i.phone, email=i.email)
            request = form.click()
            print 'step2 done',
            return request
            
    def wyr_step3(request):
        if not request: return
        forms, response = get_forms(request.get_full_url(), request.get_data())
        forms = filter(lambda f: f.has(type='textarea'), forms)
        if forms:
            form = forms[0]
            if form.fill(i.full_msg, type='textarea'):
                print 'step3 done',
                return form.production_click()
        else:
            print >> sys.stderr, response

    return wyr_step3(wyr_step2(wyr_step1(wyr_link)))

def writerep_ima(pol, ima_link, i, env={}):
    """Sends the msg along with the sender details from `i` through the form @ ima_link.
        The web page at `ima_link` typically has a single form, with the sender's details
        and subject and msg (and with a captcha img for few reps/senators).
        If it has a captcha img, the form to fill captcha is taken from env.
    """
    try:
        forms = ParseFile(StringIO(env.get('form', '')), ima_link, backwards_compat=False)
        forms = [Form(f) for f in forms]
    except: pass
    
    if not forms:
        forms, response = get_forms(ima_link)
        forms = filter(lambda f: f.has(type='textarea') , forms)

    if forms:
        f = forms[0]
        f.fill_name(i.prefix, i.fname, i.lname)
        f.fill_address(i.addr1, i.addr2)
        f.fill_phone(i.phone)
        f.fill(type='textarea', value=i.full_msg)
        captcha_val = i.get('captcha_%s' % pol, '')
        f.fill_all(city=i.city, state=i.state.upper(), zipcode=i.zip5, zip4=i.zip4, email=i.email,\
                    issue=['GEN', 'OTH'], subject=i.subject, captcha=captcha_val, reply='yes')                    
        return f.production_click()
    else:
        print 'Error: No IMA form in', ima_link,

def writerep_zipauth(pol, zipauth_link, i):
    """Sends the msg along with the sender details from `i` through the WYR system.
      This has 2 forms typically.
      Form 1 asks for zipcode and few user details 
      Form 2 asks for the subject and msg to send and other sender's details.
    """
    def zipauth_step1(f):    
        f.fill_name(i.prefix, i.fname, i.lname)
        f.fill_address(i.addr1, i.addr2)
        f.fill_phone(i.phone)
        f.fill_all(email=i.email, zipcode=i.zip5, zip4=i.zip4, city=i.city)
        if 'lamborn.house.gov' in zipauth_link:
            f.f.action = urljoin(zipauth_link, '/Contact/ContactForm.htm') #@@ they do it in ajax
        print 'step1 done',
        return f.click()
        
    def zipauth_step2(request):   
        if not request: return
        headers = {'Cookie' : 'District=%s' % i.zip5}
        forms, response = get_forms(request.get_full_url(), request.get_data(), headers)
        forms = filter(lambda f: f.has(type='textarea'), forms)
        if forms:
            f = forms[0]
            f.fill_name(i.prefix, i.fname, i.lname)
            f.fill_address(i.addr1, i.addr2)
            f.fill_phone(i.phone)
            f.fill(type='textarea', value=i.full_msg)
            f.fill_all(city=i.city, zipcode=i.zip5, zip4=i.zip4, state=i.state.upper(),
                    email=i.email, issue=['GEN', 'OTH'], subject=i.subject, reply='yes')
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
        if verbose: print 'Error: No zipauth form in', zipauth_link
        return

def get_forms(url, data=None, headers={}):
    """Returns all the forms  other than search and signup from the webpage with url `url`.
    """
    def signup_or_search(form):
        u = form.action
        try:
            form.find_control(type='textarea')
        except:
            return ('signup' in u and 'email' in u) or ('search' in u) or ('thomas.loc.gov' in u)
        else:
            return False    

    req = urllib2.Request(url, data, headers)
    response = urlopen(req) or ''
    forms = []
    if not response: return forms, response
    response = response.read()
    try:
        forms = ParseFile(StringIO(response), url, backwards_compat=False)
    except ParseError:
        forms = ParseFile(StringIO(response), url, backwards_compat=False, form_parser_class=XHTMLCompatibleFormParser)
    forms = [Form(f) for f in filter(lambda x: not signup_or_search(x), forms)]
    return forms, response

def has_message(soup, msg, tags='b'):
    """Returns if the `tags` in `soup` have `msg` in them.
    """
    bs = soup.findAll(tags)
    msg = msg.lower()
    for b in bs:
        errmsg = str(b.string).lower()
        errmsg += ' '.join(str(c) for c in b.contents)
        if (errmsg.find(msg) > -1):
            return True
    return False

def get_img_and_form(response):
    """Returns the source of captcha img(if any) and form containing it.
    """
    if not response: return None, None
    url = response.geturl()
    response = response.read()
    soup = BeautifulSoup(response)
    imgs = soup.findAll('img', attrs={'src': re.compile('.*[Cc]aptcha.*')})
    try:
        img = imgs[0]
        img_src = img.get('src', '')
        form = img.findParent('form') or ''
        captcha_src = urljoin(url, img_src)
    except Exception, details:
        print >> sys.stderr, details
        return None, None
    else:
        return captcha_src, str(form)
