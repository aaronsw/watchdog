"""
load data from govtrack.us
"""
from __future__ import with_statement
import datetime
import os

import simplejson
import web

import tools
import schema
from parse import govtrack
from settings import db

mapping = {
  'bioguideid': 'bioguideid',
  'birthday': 'birthday',
  'firstname': 'firstname',
  'gender': 'gender',
  'id': 'govtrackid',
  'lastname': 'lastname',
  'middlename': 'middlename',
  'osid': 'opensecretsid',
  'party': 'party',
  'religion': 'religion',
  'represents': 'district_id',
  'url': 'officeurl',
  'roles':'roles',
}


cong_terms = simplejson.load(file('load/manual/congress_terms.json'))
def to_dt(s): return datetime.datetime(*(map(int,s.split('-'))))
for t in cong_terms.values():
    t['startdate'] = to_dt(t['startdate'])
    t['enddate'] = to_dt(t['enddate'])

def cong_term_lookup(dstart,dend):
    if isinstance(dstart,basestring):
        dstart = to_dt(dstart)
    if isinstance(dend,basestring):
        dend = to_dt(dend)
    ret = set()
    for n,t in cong_terms.items():
        if dend < t['startdate'] or t['enddate'] < dstart:
            continue
        #print n, t['startdate'], t['enddate'], '     ', dstart, dend
        ret.add(n)
    return ret


from gen_ids import get_wd_id_GT as get_wd_id
def combine():
    watchdog_map = {}
    govtrack_map = {}

    print "Processing govtrack.us basics."
    for pol in govtrack.parse_basics():
        wd = get_wd_id(pol.id)
        if not wd: continue
        current_member = wd.get('current_member')
        watchdog_id = wd['watchdog_id']

        govtrack_map[pol.id] = watchdog_map[watchdog_id] = newpol = web.storage()

        newpol['current_member'] = current_member

        for k, v in mapping.iteritems():
            if k in pol: newpol[v] = pol[k]
    
    print "Processing govtrack.us stats."
    for pol in govtrack.parse_stats([
      'enacted', 'introduced', 'cosponsor', 'speeches']):
        if pol.id not in govtrack_map:
            continue
        else:
            newpol = govtrack_map[pol.id]
    
        if pol.get('SponsorEnacted'):
            newpol.n_bills_introduced = int(pol.NumSponsor)
            newpol.n_bills_enacted = int(pol.SponsorEnacted)
    
        if pol.get('SponsorIntroduced'):
            newpol.n_bills_debated = int(pol.NumSponsor) - int(pol.SponsorIntroduced)
    
        if pol.get('NumCosponsor'):
            newpol.n_bills_cosponsored = int(pol.NumCosponsor)
    
        if pol.get('Speeches'):
            newpol.n_speeches = int(pol.Speeches)
            newpol.words_per_speech = int(pol.WordsPerSpeech)
    
    return watchdog_map


def filter_dict(f, d):
    #return dict([(x, d[x]) for x in f and d.keys()])
    return dict([(x,d[x]) for x in d.keys() if x in f])


def unidecode(d):
    newd = {}
    for k, v in d.iteritems():
        newd[k.encode('utf8')] = v
    return newd


def load_govtrack():
    fill_dicts()


def main():
    watchdog_map = combine()
    with db.transaction():
        db.delete('congress', where='1=1')
        #db.delete('politician', where='1=1')
        for polid, pol in watchdog_map.items():
            roles = pol.pop('roles')
            # Load the Politician table
            if db.select('politician', where='id=$polid',vars=locals()): #pol.get('current_member'):
                db.update('politician', where='id=$polid', vars=locals(), 
                        **unidecode(filter_dict(schema.Politician.columns.keys(),
                            pol)))
            else:
                db.insert('politician', seqname=False, id=polid,
                        **unidecode(filter_dict(schema.Politician.columns.keys(),
                            pol)))
            # Load the Congress table
            done = set()
            for r in roles:
                repr = r.state
                if r.type == 'rep' and int(r.district) >= 0:
                    repr = '%s-%02d' % (r.state, int(r.district))
                for term in cong_term_lookup(r.startdate, r.enddate):
                    #if not db.select('congress', where='politician_id=$polid AND congress_num=$term AND district_id=$repr', vars=locals()):
                    if (polid, repr, term) not in done:
                        db.insert('congress', seqname=False, party=r.party,
                                congress_num=term, politician_id=polid,
                                current_member=pol.current_member,
                                district_id=repr)
                    done.add((polid,repr,term))


if __name__ == "__main__": 
    main()


