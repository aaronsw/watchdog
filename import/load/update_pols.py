"""Update the DB with the new politicians of 111th Congress"""

from __future__ import with_statement
import web
import simplejson
from settings import db

new_pols = simplejson.load(open('load/manual/politicians.json'))

def unidecode(d):
    newd = {}
    for k, v in d.iteritems():
        newd[k.encode('utf8')] = v
    return newd

def create_or_update(polid, dist):
    if not db.select('district', where='name=$dist', vars=locals()):
        db.insert('district', seqname=False, name=dist, state_id=dist[:2])

    if db.select('politician', where='id=$polid', vars=locals()):
        db.update('politician', where='id=$polid', district_id=dist, last_elected_year='2008', vars=locals())
    else:
        first, last = id.split('_', 1)
        first, last = first.title(), last.title()
        db.insert('politician', seqname=False, id=polid, firstname=first, lastname=last, last_elected_year='2008', district_id=dist)

def update_congress(polid, dist):
    db.insert('congress', seqname=False, politician_id=polid, district_id=dist, congress_num=111, current_member='t')

def load_new_pols():
    with db.transaction():
        db.update('congress', where="current_member='t'", current_member=False)
        for polid, pol in new_pols.items():
            district = pol['district_id']
            create_or_update(polid, district)
            update_congress(polid, district)

if __name__ == '__main__':
    load_new_pols()
