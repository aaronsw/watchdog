"""
load bill data

from: data/crawl/govtrack/us/110/{bills,rolls}
"""
from __future__ import with_statement
import os, sys, glob
import xmltramp, web
from tools import db, govtrackp

def bill2dict(bill):
    d = {}
    d['id'] = 'us/%s/%s%s' % (bill('session'), bill('type'), bill('number'))
    d['session'] = bill('session')
    d['type'] = bill('type')
    d['number'] = bill('number')
    d['introduced'] = bill.introduced('datetime')
    titles = [unicode(x) for x in bill.titles['title':] 
      if x('type') == 'short']
    if not titles:
        titles = [unicode(x) for x in bill.titles['title':]]
    d['title'] = titles[0]

    summaries = [unicode(x) for x in bill.titles['title':] 
      if x('type') == 'official']
    if not summaries:
        summaries = [unicode(x) for x in bill.titles['title':]]
    d['summary'] = summaries[0]
    
    d['sponsor'] = govtrackp(bill.sponsor().get('id'))
    return d

def fixvote(s):
    return {'0': None, '+': 1, '-': -1, 'P': 0}[s]

            
def loadbill(fn, maplightid=None):            
    bill = xmltramp.load(fn)
    d = bill2dict(bill)
    if maplightid: d['maplightid'] = maplightid
    db.insert('bill', seqname=False, **d)
    print '\r  %-25s' % d['id'],
    sys.stdout.flush()
    
    done = []
    for vote in bill.actions['vote':]:
        if not vote().get('roll'): continue
        if vote('where') in done: continue # don't count veto overrides
        done.append(vote('where'))
        
        votedoc = '%s/rolls/%s%s-%s.xml' % (
          d['session'],
          vote('where'), 
          vote('datetime')[:4], 
          vote('roll'))
        vote = xmltramp.load('../data/crawl/govtrack/us/' + votedoc)
        yeas = 0
        neas = 0
        for voter in vote['voter':]:
            if fixvote(voter('vote')) == 1:
                yeas += 1
            elif fixvote(voter('vote')) == -1:
                neas += 1
            rep = govtrackp(voter('id'))
            if rep:
                # UGLY HACK: if a politician (bob_menendez for instance) voted
                # for the same bill in both chambers of congress the insert
                # fails.
                if not db.select('vote',where="bill_id=$d['id'] AND politician_id=$rep", vars=locals()):
                    db.insert('vote', seqname=False, politician_id=rep, bill_id=d['id'], vote=fixvote(voter('vote')))
                else:
                    print "Updating:", votedoc, rep, d['id'], fixvote(voter('vote'))
                    db.update('vote', where="bill_id=$d['id'] AND politician_id=$rep", vote=fixvote(voter('vote')),vars=locals())
        db.update('bill', where="id = $d['id']", yeas=yeas, neas=neas, vars=locals())
                

def main():
    with db.transaction():
        db.delete('vote', '1=1')
        bill_ids = ', '.join((str(s.id) for s in db.select('bill', what='id')))
        db.delete('interest_group_bill_support', where='bill_id in ($bill_ids)', vars=locals()) 
        db.delete('bill', '1=1')
        for fn in glob.glob('../data/crawl/govtrack/us/*/bills/*.xml'):
            loadbill(fn)

if __name__ == "__main__":
    main()

    
