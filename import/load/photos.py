"""
find photos for politicians

from: data/crawl/house/photos/
from: data/crawl/govtrack/photos/
from: data/crawl/opensecrets/photos/
from: data/parse/politicians/govtrack.json
#from: data/crawl/votesmart/photos/ # not working yet
to:   data/parse/politicians/photos.json
"""

import os
import simplejson as json
from settings import db

def govtrack_u(govtrackid):
    return 'http://www.govtrack.us/congress/person.xpd?id=%s' % govtrackid

def bioguide_u(bioguideid):
    return 'http://bioguide.congress.gov/scripts/bibdisplay.pl?index=%s' % bioguideid

def opensecrets_u(opensecretsid):
    return 'http://opensecrets.org/politicians/summary.asp?cid=%s' % opensecretsid

def votesmart_u(votesmartid):
    return 'http://votesmart.org/bio.php?can_id=%s' % votesmartid

def govtrackcredit(govtrackid):
    """gets the credit for the GovTrack photo; credits GovTrack if we can't find it"""
    try:
        f = file('../data/crawl/govtrack/photos/%s-credit.txt')
    except IOError: # file not found
        return (govtrack_u(govtrackid), 'GovTrack')
    return f.read().split(' ', 1)

def load():
    out = {}

    pols = db.select('politician')
    #json.load(file('../data/load/politicians/govtrack.json'))

    for pol in pols:
        options = [
          (
            '../data/crawl/house/photos/%s.jpg' % pol['bioguideid'], 
            (bioguide_u(pol['bioguideid']), 'Congressional Biographical Directory')
          ),
          (
            '../data/crawl/govtrack/photos/%s.jpg' % pol['govtrackid'], 
            govtrackcredit(pol['govtrackid'])
          ),
          (
            '../data/crawl/opensecrets/photos/%s.jpg' % pol.get('opensecretsid'), 
            (opensecrets_u(pol.get('opensecretsid')), 'Center for Responsive Politics')
          ),
          (
            '../data/crawl/votesmart/photos/%s.jpg' % pol.get('votesmartid'),
            (votesmart_u(pol.get('votesmartid')), 'Project Vote Smart')
          ),
          (
            '../data/crawl/votesmart/photos/%s.JPG' % pol.get('votesmartid'),
            (votesmart_u(pol.get('votesmartid')), 'Project Vote Smart')
          )
        ]
    
        maxsize = 0
        currentfn = None
        currentcredit = None
        for fn, source in options:
            try:
                if os.stat(fn).st_size > maxsize:
                    maxsize = os.stat(fn).st_size
                    currentfn = fn
                    currentcredit = source
            except OSError: # file does not exist
                pass

        if currentfn:
            db.update('politician', where='id=$pol.id', vars=locals(), 
              photo_path=currentfn[2:],
              photo_credit_url=currentcredit[0],
              photo_credit_text=currentcredit[1]
            )

if __name__ == "__main__":
    load()
