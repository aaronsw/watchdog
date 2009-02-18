#!/usr/bin/env python
"""get capitolwords jsons and store in load/capitolwords/"""

import urllib2
import datetime
from settings import db

DATA_DIR = '../data/crawl/capitolwords'

def save_capitolwords(bioguide_id, limit=5):
    """
    save the capitolwords said by politician with bioguideid `id` in last year
    """
    today = datetime.date.today()
    from_yyyy, to_yyyy = today.year -1, today.year
    from_mm = to_mm = today.month
    from_dd = to_dd = today.day
    
    url = "http://capitolwords.org/api/lawmaker/%s/%s/%s/%s/%s/%s/%s/top%s.json" % (
                bioguide_id, from_yyyy, from_mm, from_dd, to_yyyy, to_mm, to_dd, limit)
    try:
        json = urllib2.urlopen(url).read()
    except:
        pass
    else:
        fn = "%s/%s.json" % (DATA_DIR, bioguide_id)
        file(fn, 'w').write(json)

if __name__ == "__main__":
    pols = db.select('curr_politician', what='bioguideid', where='bioguideid is not null').list()
    for p in pols[:2]:
        save_capitolwords(p.bioguideid)
