from __future__ import with_statement

import sys
import simplejson
import web
import tools
from parse import earmarks
from settings import db

reps = simplejson.load(file('../data/load/politicians/govtrack.json'))

# HACKs: hard-coding naming inconsistencies
reps['bill_young']['firstname'] = 'C.W. Bill'
reps['charles_a._wilson']['firstname'] = 'Charlie'
reps['hank_johnson']['firstname'] = 'Hank'
lastname2rep = {'Lahood': 'ray_lahood'}

ambiguous = []
for repid, rep in reps.iteritems():
    if rep['lastname'] in lastname2rep:
        ambiguous.append(rep['lastname'])
        del lastname2rep[rep['lastname']]
    else:
        lastname2rep[rep['lastname']] = repid

for repid, rep in reps.iteritems():
    if rep['lastname'] in ambiguous:
        lastname2rep[rep['lastname'] + ', ' + rep['firstname']] = repid


def cleanrow(s):
    if isinstance(s, basestring):
        s = s.strip()
        if s == '': s = None
    return s

def load():
    outdb = {}
    with db.transaction():
        db.delete('earmark', '1=1')
        done = set()
        for e in earmarks.parse_file(earmarks.EARMARK_FILE):
            de = dict(e)
            de['id'] = web.intget(de['id'])
            if not de['id'] or de['id'] in done: continue # missing the ID? come on!
            if isinstance(de['house_request'], basestring): continue # CLASSIFIED

            for k in de: de[k] = cleanrow(de[k])
            for x in ['house_member', 'house_state', 'house_party', 'senate_member', 'senate_state', 'senate_party', 'district']:
                de.pop(x)
            
            de['recipient_stem'] = tools.stemcorpname(de['intended_recipient'])
            db.insert('earmark', seqname=False, **de)
            done.add(de['id'])
        
    for e in earmarks.parse_file(earmarks.EARMARK_FILE):
        for rawRequest, chamber in zip([e.house_request, e.senate_request],[e.house_member, e.senate_member]):
            for rep in chamber:
                if rep not in lastname2rep:
                    #@@ should work on improving quality
                    pass
                else:
                    rep = lastname2rep[rep]
                    outdb.setdefault(rep, {
                      'amt_earmark_requested': 0,
                      'n_earmark_requested': 0,
                      'n_earmark_received': 0,
                      'amt_earmark_received': 0
                    })
                    outdb[rep]['n_earmark_requested'] += 1
                    requested = rawRequest or e.final_amt
                    if not isinstance(requested, float):
                        requested = e.final_amt
                    if requested:
                        outdb[rep]['amt_earmark_requested'] += requested
                    if isinstance(e.final_amt, float) and e.final_amt:
                        outdb[rep]['n_earmark_received'] += 1
                        outdb[rep]['amt_earmark_received'] += e.final_amt
    
    for rep, d in outdb.iteritems():
        db.update('politician', where='id=$rep', vars=locals(), **d)

if __name__ == "__main__": load()
