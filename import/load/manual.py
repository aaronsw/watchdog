import os, glob
import simplejson as json
import web
from settings import db
import cgitb
cgitb.enable(format='text')

DATA_DIR = 'load/manual'
current_session = 111

def unidecode(d):
    newd = {}
    for k, v in d.iteritems():
        newd[k.encode('utf8')] = v
    return newd

def items(fname):
    print 'loading', fname
    return json.load(file(DATA_DIR + '/%s.json' % fname)).iteritems()

def load_all():
    for code, state in items('states'):
        if 'aka' in state: state.pop('aka')
        db.insert('state', seqname=False, code=code, **unidecode(state))

    for name, district in items('districts'):
        db.insert('district', seqname=False, name=name, **unidecode(district))

    at_large_dists = db.select('district', what='name', where="name like '__-00'")
    for d in at_large_dists:
        state = db.select('district', what='center_lng, center_lat', where='name=$d.name[:2]', vars=locals()).list()
        if state:
            db.update('district', center_lng=state[0].center_lng, center_lat=state[0].center_lat, where='name=$d.name', vars=locals())
    
    db.update('congress', where="current_member='t'", current_member=False)
    for polid, pol in items('politicians'):
        db.insert('politician', seqname=False, id=polid, **unidecode(pol))
        db.insert('congress', seqname=False, politician_id=polid, 
                    congress_num=current_session, district_id=pol['district_id'],
                    current_member=True)

if __name__ == "__main__": load_all()
