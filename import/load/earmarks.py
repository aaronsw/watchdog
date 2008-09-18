from __future__ import with_statement

import sys
import simplejson
import web
import tools
from parse import earmarks
from settings import db
from pprint import pprint, pformat
import schema

reps = dict((x.id, x) for x in db.select('politician').list())

# HACKs: hard-coding naming inconsistencies
# Unusual name fixes
reps['bill_young']['firstname'] = 'C.W. Bill'
# Common name fixes
reps['mike_thompson']['firstname'] = 'Mike'
reps['tim_f._murphy']['firstname'] = 'Timothy'
# Dups
reps['mike_j._rogers']['firstname'] = 'Mike (MI)'
reps['mike_d._rogers']['firstname'] = 'Mike (AL)'
# Spelling
reps['corrine_brown']['firstname'] = 'Corinne'

# Force a few names into ambiguous mode
ambiguous = ['neal', 'taylor', 'jones']

lastname2rep = {}

for rep in schema.Politician.select():
    if not rep.lastname: continue
    repid = rep.id
    lastname = rep.lastname.lower()
    if lastname in lastname2rep:
        ambiguous.append(lastname)
        del lastname2rep[lastname]
    else:
        lastname2rep[lastname] = repid

for rep in schema.Politician.select():
    if not rep.lastname: continue
    repid = rep.id
    lastname=rep.lastname.lower()
    firstname=rep.firstname.lower()
    if lastname in ambiguous:
        lastname2rep[lastname + ', ' + firstname] = repid
        if rep.nickname:
            lastname2rep[lastname + ', ' + rep.nickname.lower()] = repid
        if repid in reps:
            lastname2rep[lastname + ', ' + reps[repid]['firstname'].lower()] = repid


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
            try:
                db.insert('earmark', seqname=False, **de)
            except:
                pprint(de)
                raise
            done.add(de['id'])
        
    reps_not_found = set()
    for e in earmarks.parse_file(earmarks.EARMARK_FILE):
        for rawRequest, chamber in zip([e.house_request, e.senate_request],[e.house_member, e.senate_member]):
            for rep in chamber:
                if rep.lower() not in lastname2rep:
                    #@@ should work on improving quality
                    reps_not_found.add(rep)
                    pass
                else:
                    rep = lastname2rep[rep.lower()]
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
    
    print "Did not find",len(reps_not_found),"reps:", pformat(reps_not_found)
    for rep, d in outdb.iteritems():
        db.update('politician', where='id=$rep', vars=locals(), **d)


if __name__ == "__main__": load()
