from __future__ import with_statement

import sys
import web
import tools
from parse import earmarks
from settings import db
from pprint import pprint, pformat

reps = web.storage((x.id, x) for x in db.select('politician').list())
hacks = dict()
lastname2rep = {}

# HACKs: hard-coding naming inconsistencies
hacks['jo_ann_davis'] = 'Davis, Jo Ann'
hacks['g._k._butterfield'] = 'Butterfield.'
hacks['cathy_mcmorris_rodgers'] = 'McMorris Rodger'
lastname2rep['McMorris'.lower()] = 'cathy_mcmorris_rodgers'   # Ugg, she requires multiple hacks.
# ambiguous fixes
hacks['chet_edwards'] = 'Edwards' # I think this is the correct Edwards, donna_edwards has only been a member since june 2008?
# Unusual name fixes (punctuation/spaces)
hacks['bill_young'] = 'C.W. Bill'
hacks['peter_defazio'] = 'De Fazio'
hacks['sheila_jackson-lee'] = 'Jackson Lee'
# Common name fixes
hacks['mike_thompson'] = 'Mike'
hacks['tim_f._murphy'] = 'Timothy'   #Tim is in there as BOTH Tim and Timothy
# Dups
hacks['mike_j._rogers'] = 'Mike (MI)'
hacks['mike_d._rogers'] = 'Mike (AL)'
# Spelling
hacks['corrine_brown'] = 'Corinne'
hacks['rodney_frelinghuysen'] = 'Frelinghuyson'
hacks['earl_blumenauer'] = 'Blumenaucr'
hacks['eni_faleomavaega'] = 'Faleomavaeaga'
hacks['tim_walberg'] = 'Walbergothy'

# Force a few names into ambiguous mode
ambiguous = ['neal', 'taylor', 'jones']

for repid, rep in reps.items():
    if not rep.lastname: continue
    lastname = rep.lastname.lower()
    if lastname in lastname2rep:
        ambiguous.append(lastname)
        del lastname2rep[lastname]
    else:
        lastname2rep[lastname] = repid

for repid, rep in reps.items():
    if not rep.lastname: continue
    lastname=rep.lastname.lower()
    firstname=rep.firstname.lower()
    if lastname in ambiguous:
        lastname2rep[lastname + ', ' + firstname] = repid
        if rep.nickname:
            lastname2rep[lastname + ', ' + rep.nickname.lower()] = repid
        if repid in hacks:
            lastname2rep[lastname + ', ' + hacks[repid].lower()] = repid
    if repid in hacks:
        lastname2rep[hacks[repid].lower()] = repid

def cleanrow(s):
    if isinstance(s, basestring):
        s = s.strip()
        if s == '': s = None
    return s

def load():
    outdb = {}
    done = set()
    with db.transaction():
        db.delete('earmark', '1=1')
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
                else:
                    rep = lastname2rep[rep.lower()]
                    if e.id in done: 
                        try:
                            db.insert('earmark_sponsor', seqname=False, earmark_id=e.id, politician_id=rep)
                        except:
                            print "Couldn't add %s as sponsor to earmark %d" %(rep, e.id)
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
