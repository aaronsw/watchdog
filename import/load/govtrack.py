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


ALL_PEOPLE_FILE = "../data/load/politicians/all_people.json"

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
        

def generate_ids():
    all_ids = {}
    gt_to_wd = {}
    for pol in govtrack.parse_basics():
        watchdog_id = tools.getWatchdogID(pol.get('represents'),pol.lastname)
        current_member = False
        collision = False
        # if not watchdog_id (past member/candidate), generate one.
        if watchdog_id:
            current_member = True
        else:
            watchdog_id = tools.id_ify(pol.get('firstname')+'_'+pol.get('lastname')+('_'+pol.get('namemod') if pol.get('namemod') else ''))
            if watchdog_id in all_ids and all_ids[watchdog_id] != pol.id: 
                collision = True
        gt_to_wd[pol.id] = { 'wd_id': watchdog_id }
        if current_member: gt_to_wd[pol.id]['current_member'] = True
        if collision: 
            gt_to_wd[pol.id]['collision'] = True 
            gt_to_wd[all_ids[watchdog_id]]['collision'] = True # TODO: set collision on the first one with this id.
        all_ids[watchdog_id] = pol.id

    return gt_to_wd

_gt_to_wd = None
def get_wd_id(gt_id):
    global _gt_to_wd
    if not _gt_to_wd:
        print "Loading ID mapping."
        _gt_to_wd = simplejson.load(file(ALL_PEOPLE_FILE))
    return _gt_to_wd[gt_id]


def combine():
    watchdog_map = {}
    govtrack_map = {}

    print "Processing govtrack.us basics."
    for pol in govtrack.parse_basics():
        wd = get_wd_id(pol.id)
        current_member = 'current_member' in wd and wd['current_member']
        collision = 'collision' in wd and wd['collision']
        watchdog_id = wd['wd_id']
        if collision and not current_member: 
            print "Collision(%s) not sure what to do." % watchdog_id
            continue

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
    if not os.path.isfile(ALL_PEOPLE_FILE):
        print "Generating govtrack to watchdog id mapping."
        fd = open(ALL_PEOPLE_FILE,'w')
        fd.write(simplejson.dumps(generate_ids(), indent=2, sort_keys=True))
        fd.write('\n')
        fd.close()
    main()


