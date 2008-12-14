"""
Functions to send msgs to reps and deal with captchas
"""

import sys
import re, urllib2
from urlparse import urljoin

import web
from settings import db
from wyrutils import *
from utils import captchasolver, messages, helpers, browser
from config import production_test_email, from_address, test_email
from settings import production_mode

__all__ = ["prepare", "send_msgs", "send", "writerep"]

test_mode = (not production_mode)
DEBUG = False

def prepare(pol):
    """
    Checks if the `pol`'s contact url has captcha, and if so - takes care of
    with cookies, return env with captcha url, cookies and form having captcha.
    """
    env = {}
    url = getcontact(pol).get('contact')
    b = browser.Browser()
    b.open(url)
    captchas = b.find_nodes('img', attrs={'src': re.compile('.*[Cc]aptcha.*')})
    captcha_src, form = get_src_and_form(url, captchas)
    if captcha_src:
	    env['captcha_src'], env['form'], env['cookies'] = captcha_src, form, b.get_state()
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
        if DEBUG: print handler.__name__,
        if contacttype == 'I':
            msg_sent = handler(pol, contact, i, env)
        else:
            msg_sent = handler(pol, contact, i)    
    except Exception, details:
        print >> sys.stderr, 'Error in writerep:', details
        msg_sent = False
    if not msg_sent: send_failure_report(pol, i)
    if DEBUG: print msg_sent and 'Success' or 'Failure'
    return msg_sent

def writerep_wyr(pol, wyr_link, i):
    """Sends the msg along with the sender details from `i` through the WYR system.
    The WYR system has 3 forms typically (and a captcha form for few reps in between 1st and 2nd forms).
    Form 1 asks for state and zipcode
    Form 2 asks for sender's details such as prefix, name, city, address, email, phone etc
    Form 3 asks for the msg to send.
    """
    b = browser.Browser()

    def wyr_step1(url):
        b.open(url)
        form = get_form(b, not_signup_or_search)
        # state names are in form: "PRPuerto Rico"
        state_options = form.find_control_by_name('state').items
        state_l = [s.name for s in state_options if s.name[:2] == i.state]
        form.fill_all(state=state_l[0], zipcode=i.zip5, zip4=i.zip4)
        if DEBUG: print 'step1 done',
        return form.click()
            
    def get_challenge():
        labels = b.find_nodes('label', lambda x: x.get('for') == 'HIP_response')
        if labels: return labels[0].string

    def get_wyr_form2(request):
        b.open(request)
        form = get_form(b, not_signup_or_search)
        if not form:
            if b.has_text("is shared by more than one"): raise ZipShared
            elif b.has_text("not correct for the selected State"): raise ZipIncorrect
            elif b.has_text("was not found in our database."): raise ZipNotFound
            elif b.has_text("Use your web browser's <b>BACK</b> capability "): raise WyrError
            else: raise NoForm
        else:
            challenge = get_challenge()
            if challenge:
                try:
                    solution = captchasolver.solve(challenge)
                except Exception, detail:
                    print >> sys.stderr, 'Exception in CaptchaSolve', detail
                    print >> sys.stderr, 'Could not solve:"%s"' % challenge,
                else:        
                    form.f['HIP_response'] = str(solution)
                    request = form.click()
                    form = get_wyr_form2(request)
                    return form
            else:
                return form
        
    def wyr_step2(request):
        form = get_wyr_form2(request)
        if form and form.fill_name(i.prefix, i.fname, i.lname):
            form.fill_address(i.addr1, i.addr2)
            form.fill_all(city=i.city, phone=i.phone, email=i.email)
            request = form.click()
            if DEBUG: print 'step2 done',
            return request
            
    def wyr_step3(request):
        b.open(request)
        form = get_form(b, lambda f: f.find_control_by_type('textarea'))
        if form and form.fill(i.full_msg, type='textarea'):
            if DEBUG: print 'step3 done',
            return submit_form(b, form, i)

    return wyr_step3(wyr_step2(wyr_step1(wyr_link)))

def writerep_ima(pol, ima_link, i, env={}):
    """Sends the msg along with the sender details from `i` through the form @ ima_link.
        The web page at `ima_link` typically has a single form, with the sender's details
        and subject and msg (and with a captcha img for few reps/senators).
        If it has a captcha img, the form to fill captcha is taken from env.
    """
    b = browser.Browser(env.get('cookies', []))
    b.url, b.page = ima_link, env.get('form')
    f = get_form(b, lambda f: f.find_control_by_type('textarea'))
    if not f:
        b.open(ima_link)
        f = get_form(b, lambda f: f.find_control_by_type('textarea'))

    if f:
        f.fill_name(i.prefix, i.fname, i.lname)
        f.fill_address(i.addr1, i.addr2)
        f.fill_phone(i.phone)
        f.fill(type='textarea', value=i.full_msg)
        captcha_val = i.get('captcha_%s' % pol, '')
        f.fill_all(city=i.city, state=i.state.upper(), zipcode=i.zip5, zip4=i.zip4, email=i.email,\
                    issue=['GEN', 'OTH'], subject=i.subject, captcha=captcha_val, reply='yes')
        return submit_form(b, f, i)
    else:
        print >> sys.stderr, 'Error: No IMA form in', ima_link,

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
        if DEBUG: print 'step1 done',
        return f.click()
        
    def zipauth_step2(request):
        request.add_header('Cookie', 'District=%s' % i.zip5)  #@@ done in ajax :(
        response = b.open(request)
        f = get_form(b, lambda f: f.find_control_by_type('textarea'))
        if f:
            f.fill_name(i.prefix, i.fname, i.lname)
            f.fill_address(i.addr1, i.addr2)
            f.fill_phone(i.phone)
            f.fill(type='textarea', value=i.full_msg)
            f.fill_all(city=i.city, zipcode=i.zip5, zip4=i.zip4, state=i.state.upper(),
                    email=i.email, issue=['GEN', 'OTH'], subject=i.subject, reply='yes')
            if DEBUG: print 'step2 done',
            return submit_form(b, f, i)
        else:
            print >> sys.stderr, 'no form with text area'
            if b.has_text('zip code is split between more'): raise ZipShared
            if b.has_text('Access to the requested form is denied'): raise ZipIncorrect
            if b.has_text('you are outside'): raise ZipIncorrect 
            
    b = browser.Browser()
    b.open(zipauth_link)
    form = get_form(b, lambda f: f.has(name='zip'))
    if form:
        return zipauth_step2(zipauth_step1(form))
    else:
        print >> sys.stderr, 'Error: No zipauth form in', zipauth_link

def writerep_email(pol, pol_email, i):
    name = '%s. %s %s' % (i.prefix, i.fname, i.lname)
    from_addr = '%s <%s>' % (name, i.email)

    if production_mode:
        to_addr = web.lstrips(pol_email, 'mailto:')
    elif test_mode:
        to_addr = test_email
    web.sendmail(from_addr, to_addr, i.subject, i.full_msg)
    return True

def submit_form(browser, f, i):
    """clicks the form `f` and opens the request in browser `b` and sends response."""
    if production_mode:
        request = f.click()
        response = browser.open(request)
        send_response(production_test_email, i, f.controls, response)
    elif test_mode:
        send_response(test_email, i, f.controls, response='')
    return True

def send_response(to, i, form_controls, response):
    """sends a mail to `to` to check if the form is submitted properly.
    """
    inputs ='\n'.join(['%s: %s' % (k, v) for k, v in i.items()])
    msg = 'Filled at watchdog.net:\n\n%s' % inputs

    form_values = "\n".join(["%s: %s" % (c.name, c.value) for c in form_controls])
    msg += '\n\nFilled in the last form:\n\n%s' % form_values

    if response: 
        msg +=  '\n\nResponse: \n\n' + response
    else:
        msg += '\n\n(Not Production click, no response)'

    subject = 'wyr mail'
    web.sendmail(from_address, to, subject, msg)

def send_failure_report(pol, i):
    inputs ='\n'.join(['%s: %s' % (k, v) for k, v in i.items()])
    msg = 'Filled at watchdog.net:\n\n%s' % inputs
    subject = 'Writerep to %s failed' % pol
    to = production_test_email if production_mode else test_email
    web.sendmail(from_address, to, subject, msg)    
    
def not_signup_or_search(form):
    has_textarea = form.find_control_by_type('textarea')
    if has_textarea:
        return True
    else:    
        action = form.action
        signup = 'signup' in action and 'email' in action
        search = 'search' in action or 'thomas.loc.gov' in action
        return not(search or signup)

def get_form(browser, predicate=None):
    """wrapper for browser.get_form method to return Form ojects instead of ClientForm objects"""
    f = browser.get_form(lambda f: predicate is None or predicate(Form(f)))
    if f: return Form(f)

def get_src_and_form(url, imgs):
    """Returns the source of captcha img(if any) and form containing it.
    """
    try:
        img = imgs[0]
        img_src = img.get('src', '')
        form = repr(img.findParent('form')) or ''
        captcha_src = urljoin(url, img_src)
    except Exception, details:
        print >> sys.stderr, details
        return None, None
    else:
        return captcha_src, form
