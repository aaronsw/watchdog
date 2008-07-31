import sys
import simplejson
from parse import earmarks

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

outdb = {}

for earmark in earmarks.getEarmarks('../data/crawl/taxpayer/bigkahuna.xls'):
    for rawRequest,chamber in zip([earmark.houseRequestDollars, earmark.senateRequestDollars],[earmark.houseMembers,earmark.senateMembers]):
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
                requested = rawRequest or earmark.finalAmountDollars
                if not isinstance(requested, float):
                    requested = earmark.finalAmountDollars
                if requested:
                    outdb[rep]['amt_earmark_requested'] += requested
                if not isinstance(earmark.finalAmountDollars, float) or not earmark.finalAmountDollars:
                    continue
                outdb[rep]['n_earmark_received'] += 1
                outdb[rep]['amt_earmark_received'] += earmark.finalAmountDollars

print simplejson.dumps(outdb, indent=2, sort_keys=True)
