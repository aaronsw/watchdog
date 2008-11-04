#!/usr/bin/env python
# encoding: utf-8
"""
writerep.py
Write Your Representative
"""
import sys
import urllib2
from ClientForm import ParseFile, ParseError, XHTMLCompatibleFormParser
from BeautifulSoup import BeautifulSoup
from StringIO import StringIO

import web
import captchasolver, forms, helpers, auth
from settings import db, render, production_mode
from users import fill_user_details, update_user_details
from wyrutils import * #@@@ put all the list here 
from config import test_email

test_mode = (not production_mode)

urls = (
  '', 'redir',
  '/', 'write_your_rep',
  '/test', 'wyr_test',
  '/verifyzip', 'verify_zip',
  '/getcaptcha', 'get_captcha'
)

class redir:
    def GET(self): raise web.seeother('/')

def has_message(soup, msg, tags='b'):
    bs = soup.findAll(tags)
    msg = msg.lower()
    for b in bs:
        errmsg = str(b.string).lower()
        errmsg += ' '.join(str(c) for c in b.contents)
        if (errmsg.find(msg) > -1):
            return True
    return False

def get_forms(url, data=None, headers={}):    
    def signup_or_search(u):
        return ('signup' in u) or ('search' in u) or ('thomas.loc.gov' in u)

    req = urllib2.Request(url, data, headers)
    response = urlopen(req)
    if response: response = response.read()
    try:
        forms = ParseFile(StringIO(response), url, backwards_compat=False)
    except ParseError:
        forms = ParseFile(StringIO(response), url, backwards_compat=False, form_parser_class=XHTMLCompatibleFormParser)
    except:
        forms = []
    
    forms = [Form(f) for f in filter(lambda x: not signup_or_search(x.action), forms)]
    return forms, response or ''

def writerep_email(pol_email, pol, zipcode, state, prefix, fname, lname,
            addr1, city, phone, email, subject, msg, addr2='', addr3='', zip4=''):
            
    name = '%s. %s %s' % (prefix, fname, lname)
    from_addr = '%s <%s>' % (name, email)
  
    if production_mode:
        to_addr = web.lstrips(pol_email, 'mailto:')
    elif test_mode:
        to_addr = test_email
    #@@@@ msg has to be composed    
    web.sendmail(from_addr, to_addr, subject, msg)
    return True        

def writerep_wyr(wyr_link, pol, zipcode, state, prefix, fname, lname,
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

def writerep_ima(ima_link, pol, zipcode, state, prefix, fname, 
                 lname, addr1, city, phone, email, subject, msg, 
                 addr2='', addr3='', zip4='', captcha=''):

    forms, response = get_forms(ima_link)
    forms = filter(lambda f: f.has(type='textarea') , forms)
    
    if forms:
        f = forms[0]
        f.fill_name(prefix, fname, lname)
        f.fill_address(addr1, addr2, addr3)
        f.fill_all(city=city, state=state.upper(), zipcode=zipcode, zip4=zip4, email=email, issue=['GEN', 'OTH'])
        f.fill_phone(phone)
        f.fill(type='textarea', value=msg)
        f.fill_all(captcha=captcha)
        return f.production_click()
    else:
        print 'Error: No IMA form in', ima_link,

def writerep_zipauth(zipauth_link, pol, zipcode, state, prefix, fname, 
                     lname, addr1, city, phone, email, subject, msg, 
                     addr2='', addr3='', zip4=''):
            
    def zipauth_step1(f):    
        f.fill_name(prefix, fname, lname)
        f.fill_address(addr1, addr2, addr3)
        f.fill_all(email=email, zipcode=zipcode, zip4=zip4, city=city)
        f.fill_phone(phone)
        if 'lamborn.house.gov' in zipauth_link:
            f.f.action = urljoin(zipauth_link, '/Contact/ContactForm.htm') #@@ they do it in ajax
        print 'step1 done',
        return f.click()
        
    def zipauth_step2(request):   
        if not request: return
        headers = {'Cookie' : 'District=%s' % zipcode}
        forms, response = get_forms(request.get_full_url(), request.get_data(), headers)
        forms = filter(lambda f: f.has(type='textarea'), forms)
        if forms:
            f = forms[0]
            f.fill_name(prefix, fname, lname)
            f.fill_address(addr1, addr2, addr3)
            f.fill_all(city=city, zip=zipcode, email=email, issue=['GEN', 'OTH'])
            f.fill_phone(phone)
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
    
def getcontact(pol):
    r = db.select('pol_contacts', what='contact, contacttype', where='politician_id=$pol', vars=locals())
    if r: 
        r = r[0]                
        return r.contact, r.contacttype
    else:
        return None, None    
        
def writerep(pol, zipcode, prefix, fname, lname, 
             addr1, city, phone, email, subject, msg, addr2='', addr3='', zip4='', captcha=''):
    dist = pol2dist(pol)
    state = dist and dist[:2]
    prefix = prefix.rstrip('.') #few forms take only Mr, Ms etc.
    args = locals(); args.pop('dist')
    
    href, contacttype = getcontact(pol)
    if contacttype not in ['E', 'W', 'I', 'Z']: return False
    d = dict(E='pol_email', W='wyr_link', I='ima_link', Z='zipauth_link')
    args[d[contacttype]] = href
    if contacttype != 'I': args.pop('captcha')
         
    handlers = dict(E=writerep_email, W=writerep_wyr, I=writerep_ima, Z=writerep_zipauth)
    print handlers[contacttype].__name__,
    
    msg_sent = handlers[contacttype](**args)    
    return msg_sent
             
class write_your_rep:
    def __init__(self):
        self.msg_id = None
        self.dist = None
        self.pol = None

    def set_dist(self, i):
        try:
            self.dist = getdists(i.zipcode, i.zip4, i.addr1+i.addr2)[0]
        except KeyError:
            raise ZipIncorrect
            
    def set_pol(self, i):
        if not self.dist:
            self.set_dist(i)
        self.pol = db.select('politician', what='id', 
                                where='politician.district_id=$self.dist',
                                vars=locals())[0].id
                
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
        msg_id = db.insert('wyr', politician=self.pol, subject=subj, message=msg, sender=user_id, sent=False)
        return msg_id

    def send_msg(self, i, wyrform, pform=None):
        pol = self.pol
        captcha_src = (not i.get('captcha')) and get_captcha_src(pol)
        if captcha_src:
            set_captcha(wyrform, captcha_src)
            msg = 'Please fill in the captcha verification below'
            helpers.set_msg(msg, msg_type='note')
            raise CaptchaException

        email = 'p-%s@watchdog.net' % (self.msg_id)
        try:
            msg_sent = writerep(pol=pol,
                        prefix=i.prefix, lname=i.lname, fname=i.fname,
                        addr1=i.addr1, addr2=i.addr2, city=i.city,
                        zipcode=i.zipcode, zip4=i.zip4,
                        phone=web.numify(i.phone), email=email, subject=i.ptitle, msg=i.msg,
                        captcha=i.get('captcha', ''))
        except:
            msg_sent = False
                            
        if not pform: update_user_details(i)
        return msg_sent

    def save_and_send_msg(self, i, wyrform, pform=None):
        self.set_pol(i)
        msg_id = self.save_msg(i.ptitle, i.msg)  
        self.set_msg_id(msg_id)
        msg_sent = self.send_msg(i, wyrform, pform)
        if msg_sent == True:
            db.update('wyr', where='id=$msg_id', sent=True, vars=locals())
        return msg_sent    
    
    def GET(self, form=None):
        if not form:
            form = forms.wyrform()
            fill_user_details(form)
            add_captcha(form)
            
        useremail = helpers.get_loggedin_email() or helpers.get_unverified_email()    
        msg, msg_type = helpers.get_delete_msg()
        return render.writerep(form, useremail=useremail, msg=msg)

    def POST(self):
        i = web.input()
        wyrform = forms.wyrform()
        if wyrform.validates(i):
            auth.assert_login(i)
            try:
                status = self.save_and_send_msg(i, wyrform)
            except CaptchaException:
                msg, msg_type = helpers.get_delete_msg()
                return render.writerep(wyrform, msg)
            else:
                if status:
                    p = db.select('politician', what='firstname, middlename, lastname',
                                    where='id=$self.pol', vars=locals())[0]
                    polstr = '<a href="/p/%s">%s %s %s</a>' % (self.pol, p.firstname, p.middlename, p.lastname)  
                    helpers.set_msg('Your message has been sent to %s.' % polstr)
                else:
                    helpers.set_msg('Sorry, your message has NOT been sent.', 'error')
            raise web.seeother('/')
        else:
            return self.GET(wyrform)

class wyr_test:
    def get_from_input(self, key, input=None):
       if not input: input = web.input()
       possibles = name_options[key]
       for name in possibles:
           for k in input.keys():
               if name in k.lower():
                   return input.get(k)
    def POST(self):
        i = web.input()
        to_addr = test_email
        from_addr = self.get_from_input('email', i) or ''
        subject = self.get_from_input('issue', i) or ''
        msg = self.get_from_input('message', i) or ''
        web.sendmail(from_addr, to_addr, subject, msg)
        return 

class verify_zip:
    def POST(self):
        i = web.input()
        dists = getdists(i.zipcode, i.zip4, i.address)
        if len(dists) == 1:
            return dists[0]
        else:
            return len(dists)    
    
class get_captcha:
    def GET(self):
        i = web.input()
        pol = dist2pol(i.dist)
        src = get_captcha_src(pol)
        if src:
            wyr = forms.wyrform()
            set_captcha(wyr, src)
            return '<tr><td colspan=3><label for="captcha">Verification</label>'+ wyr.captcha.pre + wyr.captcha.render()+'</td></tr>'

app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()

