import sys
import web
from settings import db

import urllib2 
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup
from ClientForm import ParseResponse
import simplejson

def urlopen(url, data=None):
    try:
        return urllib2.urlopen(url, data)
    except Exception, detail:
        print >> sys.stderr, 'Error opening %s, %s' % (url, detail)
        return None

def write(d, filename):
    f = open(filename, 'w')
    simplejson.dump(d, f, indent=2, sort_keys=True)
    f.close()
    
def find_all():
    d = {}
    rs = db.query("select district, officeurl from politician").list()
    for r in rs:
        dist, home = r.district, r.officeurl
        d[dist] = dict(wyrform=None, ima=None, zipauth=None, captcha=None, contactform=None)
        if home:
            if has_wyr(dist): 
                d[dist]['wyrform'] = True
            else:    
                formtype, link = get_contactform_link(home)
                if not formtype:
                    contact_page = get_contact_page(home)
                    formtype, link = get_contactform_link(contact_page)
                
                isima, iszipauth = formtype=='ima', formtype == 'zipauth'
                if isima or iszipauth: 
                    d[dist] = dict(wyrform=None, ima=isima, zipauth=iszipauth, captcha=has_captcha(link), contactform=link)
            print >> sys.stderr, d[dist]        
    return d            
            
def get_link_with(links, lstr):
    """ 
    Returns link with any of the `lstr` in the link or its text, if exists.
    """
    if not isinstance(lstr, list): lstr = [lstr]
        
    for s in lstr:
        for link in links:
            href = link.get('href', '') or link.get('HREF', '')
            text = link.contents and str(link.contents[0]) or ''
            if (s in href.lower()) or (s in text.lower()):
                 return href           
                
def get_contact_page(url):    
    """
    Takes home page of politician and returns the url for contact page.
    """
    """
        >>> get_contact_page("http://kanjorski.house.gov/")
        u'http://kanjorski.house.gov/index.php?option=com_content&task=view&id=37&Itemid=13'
        >>> get_contact_page("http://flake.house.gov/")
        u'http://flake.house.gov/Contact/'
        >>> get_contact_page("http://www.house.gov/blackburn")
        u'http://blackburn.house.gov/Contact/'
        >>> get_contact_page("http://www.house.gov/olver")
        u'http://www.house.gov/olver/contactme.html'
        
    """
    response = urlopen(url)
    
    try:        
        soup = BeautifulSoup(response)
    except:
        return ''    
    links = soup.findAll({'a': True, 'area':True})

    if len(links) == 1: return get_contact_page(links[0].get('href', ''))

    contact_link = get_link_with(links, ['contact', 'email'])
    if contact_link:
        return urljoin(response.geturl(), contact_link)

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
    response = urlopen(url)
    if response: 
        soup = BeautifulSoup(response)
        return bool(soup.findAll('img', attrs={"src": re.compile(".*[Cc]aptcha.*")}))
    return False
    
def has_ima_or_zipauth(url, data=None):
    if not url: return None, None
    try:
        response = urlopen(url, data)
        forms = ParseResponse(response, backwards_compat=False)
    except:
        return None, None
    else:
        if filter(has_textarea, forms): return 'ima', url
        if filter(has_zipauth, forms): return 'zipauth', url
    return None, None    

def get_contactform_link(url):
    formtype, _url = has_ima_or_zipauth(url)
    if formtype: return formtype, _url
    
    response = urlopen(url)
    try:    
        soup = BeautifulSoup(response)
    except:
        return None, None
            
    links = soup.findAll({'a': True})
    ima_link = get_link_with(links, ['ima/', 'issues_subscribe'])
    formtype, url = has_ima_or_zipauth(urljoin(response.geturl(), ima_link))
    if formtype: return formtype, url

    zipauth_link = get_link_with(links, ['zipauth', 'zip_auth'])    
    formtype, url = has_ima_or_zipauth(urljoin(response.geturl(), zipauth_link))
    if formtype: return formtype, url
    
    return None, None
    
#--------------------------------------------
    
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
        form = ParseResponse(response, backwards_compat=False)[1]
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
        soup = BeautifulSoup(response)
    except:
        return False
    return len(soup.findAll('form')) == 2       


if __name__ == "__main__":
    #import doctest
    #doctest.testmod()
    write(find_all(), 'wyr.json')