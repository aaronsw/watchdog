import sys
import simplejson
from urllib2 import urlopen
from ClientForm import ParseResponse, ParseFile
from settings import db
from BeautifulSoup import BeautifulSoup

def has_textarea(f):
    try:
        c = f.find_control(type='textarea')
    except:
        return False
    else:
        return True

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
    
def is_email(s):
    return '@' in s
    
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

def has_wyr(dist):
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

def get_wyr_forms(dists):
    d = {}
    wyr_url = 'https://forms.house.gov/wyr/welcome.shtml'
    for dist in filter(has_wyr, dists):
        d[dist] = dict(contact=wyr_url, contacttype='wyr', captcha=False)
    return d    
            
def typeof(url):
    ctype = (is_email(url) and 'email') 
    if not ctype and not is_wyr(url):
        try:
            response = urlopen(url)
            forms = ParseResponse(response, backwards_compat=False)
        except Exception, details:
            #print >> sys.stderr, url, details
            pass
        else:
            ctype = (any_ima(forms) and 'ima') or (any_zipauth(forms) and 'zipauth')
    return ctype
        
def get_votesmart_contacts(dists):
    d = {}
    websites = simplejson.load(file('../data/crawl/votesmart/websites.json'))
    dists = tuple(dists)
    rs = db.select('politician', what='district, votesmartid',
                where='district in $dists', vars=locals())
    
    for r in rs:
        url = None
        contact = websites.get(r.votesmartid, {})
        if 'office' in contact.keys():
            for addr in contact['office']:
                if addr['webAddressType'] == 'Email':
                    url = addr['webAddress']
                if not url and addr['webAddressType'] == 'Webmail':
                    url = addr['webAddress']
            contacttype = url and typeof(url)
            if contacttype:
                captcha = (type == 'ima') and has_captcha(url)
                d[r.district] = dict(contact=url, contacttype=contacttype, captcha=captcha)    
    return d
        
def main(fname='wyr.json'):
    #@@@ PVS data has few false positives for WYR form. 
    # So, better get reps having wyr forms in house.gov and then proceed to PVS data.
    all_dists = set(r.name for r in db.select('district', what='name'))
    d = get_wyr_forms(all_dists)
    remaining_dists = list(all_dists - set(d.keys()))
    d.update(get_votesmart_contacts(remaining_dists))
    f = file(fname, 'w')
    simplejson.dump(d, f, indent=2, sort_keys=True)                     
    
if __name__ == '__main__':
    main()               
