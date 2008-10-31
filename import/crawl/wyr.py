import sys
import simplejson as json
from urllib2 import urlopen
from ClientForm import ParseResponse, ControlNotFoundError, AmbiguityError
from settings import db
from BeautifulSoup import BeautifulSoup

manual_websites = '../import/load/manual/websites.json'
votesmart_websites = '../data/crawl/votesmart/websites.json'

def is_email(s):
    return ('@' in s) and not s.startswith('http://')
    
def has_textarea(f):
    try:
        c = f.find_control(type='textarea')
    except ControlNotFoundError:
        return False
    except AmbiguityError:  #more than 1 textarea
        return True
    else:
        return True    

def pol2dist(pol):
    try:
        return db.select('politician', what='district_id', where='politician.id=$pol', vars=locals())[0].district_id
    except KeyError:
        return

def has(f, s):
    for c in f.controls:
        if c.name and s in c.name.lower():
            return True
    return False
            
def has_zipauth(f):
    return has(f, 'zip')
    
def has_captcha(url):
    import re
    try:
        response = urlopen(url)
        soup = BeautifulSoup(response)
    except Exception, details:
        print >> sys.stderr, url, details
        return False
    else:        
        return bool(soup.findAll('img', attrs={"src": re.compile(".*[Cc]aptcha.*")}))

def any_zipauth(forms):
    return any(has_zipauth(f) for f in forms)
    
def any_ima(forms):
    return any(has_textarea(f) for f in forms)                   
    
def is_wyr(s):
    return ('www.house.gov/writerep' in s) or ('https://forms.house.gov/wyr/welcome.shtml' == s)

def getdistzipdict(zipdump):
    """returns a dict with district names as keys zipcodes falling in it as values"""
    d = {}
    for line in zipdump.strip().split('\n'):
        zip5, zip4, district = line.split('\t')
        d[district] = (zip5, zip4)
    return d

dist_zip_dict =  getdistzipdict(file('../utils/zip_per_dist.tsv').read())

def getzip(dist):
    try:
        return dist_zip_dict[dist]
    except:
        return '', ''    

def has_wyr(pol):
    dist = pol2dist(pol)
    if len(dist) == 2: return False # senators don't have forms in WYR system

    try:
        response = urlopen("https://forms.house.gov/wyr/welcome.shtml")
        form = ParseResponse(response, backwards_compat=False)[1] #first form is of search
    except:
        return False

    state = dist[:2]
    state_options = form.find_control(name='state').items
    state_l = [s.name for s in state_options if s.name[:2] == state]
    zip5, zip4 = getzip(dist)

    form['state'] = state_l
    form['zip'] = zip5
    form['zip4'] = zip4
    request = form.click()
    try:
        response = urlopen(request.get_full_url(), request.get_data())
        forms = ParseResponse(response, backwards_compat=False)
    except:
        return False
    else:    
        return len(forms) == 2       

def get_wyr_forms(pols):
    d = {}
    wyr_url = 'https://forms.house.gov/wyr/welcome.shtml'
    for pol in filter(has_wyr, pols):
        d[pol] = dict(contact=wyr_url, contacttype='wyr', captcha=False)
    return d    
            
def getformtype(url):
    """
    In the given url, checks for existence of 'ima' or 'zipauth' forms. If neither of them is there,
    it looks of for a one in frames, if any.
    Returns the form type, if there is a one.
    """    
    if is_wyr(url):
        return 'https://forms.house.gov/wyr/welcome.shtml', 'wyr'
    
    try:
        response = urlopen(url)
        forms = ParseResponse(response, backwards_compat=False)
    except Exception, details:
        #print >> sys.stderr, url, details
        pass
    else:
        formtype = (any_ima(forms) and 'ima') or (any_zipauth(forms) and 'zipauth')
        if formtype:
            return response.geturl(), formtype 
        else:
            try:
                soup = BeautifulSoup(urlopen(url))
            except:
                pass
            else:
                frame = soup.findAll(['iframe', 'frame'])
                if frame: 
                    url = frame[0].get('src')
                    return getformtype(url)
            
    return None, None        
            
        
def get_votesmart_contacts(pols):
    d = {}
    websites = json.load(file(votesmart_websites))
    pols = tuple(pols)
    rs = db.select('politician', what='id, votesmartid', where='id in $pols', vars=locals())
    
    for r in rs:
        _url, contacttype = None, None
        contact = websites.get(r.votesmartid, {})
        if 'office' in contact.keys():
            for addr in contact['office']:
                if addr['webAddressType'] == 'Email':
                    email = addr['webAddress']
                    if email.endswith('mail.house.gov') or email.endswith('mail.senate.gov'):
                        _url, contacttype = 'mailto:' + email, 'email'
                if not _url and addr['webAddressType'] == 'Webmail':
                    url = addr['webAddress']
                    _url, contacttype = getformtype(url)
						
            if contacttype and contacttype != 'wyr':
                captcha = (contacttype == 'ima') and has_captcha(url)
                d[r.id] = dict(contact=_url, contacttype=contacttype, captcha=captcha)    
    return d

def get_manual_contacts(pols):
    d = {}
    items = json.load(file(manual_websites))
    for pol in pols:
        url = items.get(pol, dict(contact=''))['contact']
        if url:
            if is_email(url):
                _url, contacttype = 'mailto:' + url, 'email'
            else:
                _url, contacttype = getformtype(url)
            if contacttype:
                captcha = (contacttype == 'ima') and has_captcha(_url)
                d[pol] = dict(contact=_url, contacttype=contacttype, captcha=captcha)
    return d        
        
def main(fname='../data/crawl/votesmart/wyr.json'):
    #@@@ PVS data has few false positives for WYR form. 
    # So, better get reps having wyr forms in house.gov and then proceed to PVS data and then to manually created json
    all_pols = set(r.id for r in db.select('politician', what='id'))
    
    d = get_wyr_forms(all_pols)
    remaining_pols = list(all_pols - set(d.keys()))

    d.update(get_votesmart_contacts(remaining_pols))
    remaining_pols = list(all_pols - set(d.keys()))
    
    d.update(get_manual_contacts(all_pols))
    
    f = file(fname, 'w')
    json.dump(d, f, indent=2, sort_keys=True)                     
    
if __name__ == '__main__':
    main()               
