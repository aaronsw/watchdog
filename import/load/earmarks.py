import sys
import simplejson
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

def load():
    outdb = {}
    
    for e in earmarks.parse_file(earmarks.EARMARK_FILE):
        for rawRequest, chamber in zip([e.usd_house_request, e.usd_senate_request],[e.house_member, e.senate_member]):
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
                    requested = rawRequest or e.usd_final
                    if not isinstance(requested, float):
                        requested = e.usd_final
                    if requested:
                        outdb[rep]['amt_earmark_requested'] += requested
                    if isinstance(e.usd_final, float) and e.usd_final:
                        outdb[rep]['n_earmark_received'] += 1
                        outdb[rep]['amt_earmark_received'] += e.usd_final
    
    for rep, d in outdb.iteritems():
        db.update('politician', where='id=$rep', vars=locals(), **d)

if __name__ == "__main__": load()
