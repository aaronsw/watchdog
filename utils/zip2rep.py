"""
zip2rep: convert locations into congressional districts
http://www.aaronsw.com/2002/zip2rep/

The function you probably want is `zip2dist` (the last one).
If you use this software, please send me an email letting me know.
If you like this software, you should support gerrymandering reform:
http://fairvote.org/?page=564
"""

__author__ = "Aaron Swartz <me@aaronsw.com>"
__version__ = "0.3"
__license__ = "Public domain"

"""
Revision history:

2008-04-11: 0.3  - fix bug causing us to lose Indiana (sorry, Indiana!)
2008-04-04: 0.21 - zip2rep now returns [] on invalid zipcodes
2008-03-25: 0.2  - fix bad bug with last district getting cut off (tx Jordan)
2008-03-23: 0.1  - initial version
"""

import urllib, re
u = "http://frwebgate.access.gpo.gov/cgi-bin/getdoc.cgi?dbname=%s_congressional_directory&docid=%sth_txt-"

def count(lst):
    """
    Takes a list of items and counts the values, returning 
    a sorted list of (value, count) pairs.
    
        >>> count(['a', 'a', 'a', 'c', 'a'])
        [(4, 'a'), (1, 'c')]
    """
    d = {}
    for item in lst:
        if item in d:
            d[item] += 1
        else:
            d[item] = 1
    out = [(v, k) for k, v in d.iteritems()]
    out.sort(reverse=True)
    return out

def cleanzips(ziplisting):
    def tozip(n):
        return str(n).zfill(5)
    s = ziplisting
    s = s.replace('\n', '').replace(' ', '') # remove whitespace
    s = s.split(',')
    ziplisting = s
    out = []
    for zcode in ziplisting:
        if '-' in zcode: # e.g. "20210-13"
            head, tail = zcode.split('-')
            out.append(head)
            head = int(head)
            assert tail.isdigit() # sanity check
            while not tozip(head).endswith(tail):
                head += 1
                out.append(tozip(head))
        else:
            out.append(zcode) # e.g. "20080"
    return out

r_pagenum = re.compile('\[\[Page \d+\]\]')
r_strong = re.compile('\</?strong\>')
r_zip = re.compile(r'ZIP Codes: (.*?)(?:\*  \*  \*|</pre>)', re.DOTALL)
r_state = re.compile('([A-Z][A-Z]) \d\d\d\d\d')

def parseone(u):
    t = urllib.urlopen(u).read()
    t = r_pagenum.sub('', t)
    t = r_strong.sub('', t)
    
    states = [s for c, s in count(r_state.findall(t)) if s != 'DC']
    if states:
        state = states[0]
    else: # must be DC
        state = 'DC'
    
    ziplist = [cleanzips(x) for x in r_zip.findall(t)]
    if len(ziplist) == 1: # at-large district
        yield (state + '-00', ziplist[0])
    else:
        for n, zips in enumerate(ziplist):
            yield (state + '-' + str(n+1).zfill(2), zips)

def parseall(session=110):
    """
    Parses the entire Congressional Directory into an iterator of
    2-tuples consisting of district code and a list of zip codes, e.g.:
    
        ('PR-00', ['00601', '00602', '00603', ...])
    """
    # workaround for missing data
    missing = {
      110: {
        'TX-25': ['78701'],
        'TX-21': ['78701']
      }
    }
    
    for i in range(2, 2 + 55):
        for item in parseone(u % (session, session) + str(i)):
            if item[0] in missing.get(session, {}):
                yield item[0], item[1] + missing[session][item[0]]
            else:
                yield item
    
def zipdict(session=110):
    """
    Returns a dictionary mapping zip codes to congressional districts:
    
    {
      '00601': ['PR-00'],
      '20231': ['DC-00', 'VA-08'],
      ...
    }
    """
    
    d = {}
    for district, zipcodes in parseall():
        for zipcode in zipcodes:
            d.setdefault(zipcode, [])
            d[zipcode].append(district)
    return d

def dumpzipdict(zipd):
    """
    Serializes the output of `zipdict` to a format like:
    
        00601: PR-00
        20231: DC-00 VA-08
        ...
    """
    out = []
    for k, v in zipd.iteritems():
        out.append(k + ': ')
        out.append(' '.join(v))
        out.append('\n')
    return ''.join(out)

def parsezipdict(zipdump):
    """
    Reparses the output of `dumpzipdict`.
    """
    d = {}
    for line in zipdump.strip().split('\n'):
        zipcode, districts = line.split(': ', 1)
        districts = districts.split(' ')
        d[zipcode] = districts
    return d

try:
    # file('zipdict.txt', 'w').write(dumpzipdict(zipdict()))
    myzipdict = parsezipdict(file('zipdict.txt', 'r').read())
except IOError:
    try:
        import os, sys
        myzipdict = parsezipdict(file(
          os.path.abspath(os.path.dirname(sys.modules[__name__].__file__)) +
          '/zipdict.txt', 'r').read())
    except IOError:
        pass

class BadAddress(Exception): pass
geocoder_u = "http://rpc.geocoder.us/service/csv?address="
def geocoder(addr):
    """
    Runs an address thru geocoder.us, returning a list like:
    
        ['38.898748', '-77.037684', '1600 Pennsylvania Ave NW',
         'Washington', 'DC', '20006']
    
    TODO: handle more errors
    """
    u = geocoder_u + urllib.quote(addr)
    t = urllib.urlopen(u).read()
    if t.startswith('2: '):
        raise BadAddress, t
    return t.split(',')

govtrack_u = 'http://www.govtrack.us/perl/wms/get-region.cgi?layer=cc-pac&lat=%s&long=%s&format=text'
def govtrack(lat, lng):
    """
    Runs a (lat, lng) pair thru govtrack.us, returning a 
    Congressional District (e.g. 'VA-01').
    
    TODO: handle errors
    """
    
    u = govtrack_u % (lat, lng)
    t = urllib.urlopen(u).read()
    distparts = t.split('\t')[0].split('/')
    state = distparts[-4]
    distnum = distparts[-1]
    return state.upper() + '-' + distnum.zfill(2)
    
def zip2dist(zipcode, addr=None):
    """
    Takes a zip code and an optional address and returns a list of 
    matching congressional districts.
        
        >>> zip2dist('12345')
        ['NY-21']
        >>> zip2dist('90210')
        ['CA-30']
        >>> zip2dist('12010')
        ['NY-20', 'NY-21', 'NY-23']
        >>> zip2dist('12010', '10 E Main St')
        ['NY-21']

    TODO: handle errors
    """
    try:
        dists = myzipdict[zipcode]
    except KeyError:
        return []
    if len(dists) == 1 or addr is None:
        return dists
    else:
        lat, lng = geocoder(addr + ', ' + zipcode)[:2]
        return [govtrack(lat, lng)]

if __name__ == "__main__":
    #print "Generating the zipdict (this will take some time and bandwidth)..."
    #file('zipdict.txt', 'w').write(dumpzipdict(zipdict()))
    print "Get the latest zipdict.txt file at http://watchdog.net/about/api#zip2rep"
