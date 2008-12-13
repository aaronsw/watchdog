"""
Loads the phone numbers of politicians into DB from votesmart offices data
"""

from __future__ import with_statement
import sys
import simplejson
from settings import db
from urllib2 import urlopen
import re

votesmart_offices = '../data/crawl/votesmart/offices.json'
    
def get_votesmart_phones(pols):
    def _get(ph, phtype):
        try:
            return ph.get(phtype, '').replace('-', '').split()[0]
        except IndexError: pass

    d = {}
    offices = simplejson.load(file(votesmart_offices))
        
    for pol in pols:
        polid = pol.id
        contact = offices.get(pol.votesmartid, {})
        offs = contact.get('office', [])
        for o in offs:
            phones, address = o.get('phone', {}), o.get('address', {})
            city = address.get('city', '')
            phone1 = _get(phones, 'phone1')
            phone2 = _get(phones, 'phone2')
            tollfree = _get(phones, 'tollFree')
            d[(polid, city)] = dict(phone1=phone1, phone2=phone2, tollfree=tollfree)
    return d

def get_all_phones():
    """return list of all phones in house from 'http://clerk.house.gov/member_info/mcapdir.html'"""
    response = urlopen('http://clerk.house.gov/member_info/mcapdir.html').read()
    r = re.compile('\d{3}-\d{4}')
    return r.findall(response)

#phones_from_house = get_all_phones()

def load_phones(phones):
    with db.transaction():
        db.delete('pol_phones', '1=1')
        for k, v in phones.items():
            polid, city = k
            db.insert('pol_phones', seqname=False, politician_id=polid, city=city, **v)
    
if __name__ == '__main__':
    pols = db.select('politician', what='id, votesmartid')
    phones = get_votesmart_phones(pols)
    load_phones(phones)
