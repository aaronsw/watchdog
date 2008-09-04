"""
load bill data

from: data/crawl/govtrack/us/110/{bills,rolls}
"""
from __future__ import with_statement
import os
import sys
import glob

import xmltramp
import web

from tools import db, govtrackp

DATA_DIR='../data/'
GOVTRACK_CRAWL=DATA_DIR+'/crawl/govtrack'

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

            
vote_list = {}
bill_list =[]
def loadbill(fn, maplightid=None, batch_mode=False):            
    bill = xmltramp.load(fn)
    d = bill2dict(bill)
    if maplightid: d['maplightid'] = maplightid
    else: d['maplightid'] = None
    if not batch_mode: db.insert('bill', seqname=False, **d)
    print >>sys.stderr,'\r  %-25s' % d['id'],
    sys.stderr.flush()
    
    done = []
    d['yeas']=d['neas']=0
    for vote in bill.actions['vote':]:
        if not vote().get('roll'): continue
        if vote('where') in done: continue # don't count veto overrides
        done.append(vote('where'))
        
        votedoc = '%s/rolls/%s%s-%s.xml' % (
          d['session'],
          vote('where'), 
          vote('datetime')[:4], 
          vote('roll'))
        vote = xmltramp.load(GOVTRACK_CRAWL+'/us/' + votedoc)
        yeas = 0
        neas = 0
        for voter in vote['voter':]:
            if fixvote(voter('vote')) == 1:
                yeas += 1
            elif fixvote(voter('vote')) == -1:
                neas += 1
            rep = govtrackp(voter('id'))
            if rep:
                if batch_mode:
                    vote_list['%(bill_id)s\t%(politician_id)s'% {'bill_id':d['id'], 'politician_id':rep}]={'bill_id':d['id'], 'politician_id':rep, 'vote':fixvote(voter('vote'))}
                else:
                    if not db.select('vote',where="bill_id=$d['id'] AND politician_id=$rep", vars=locals()):
                        db.insert('vote', seqname=False, politician_id=rep, bill_id=d['id'], vote=fixvote(voter('vote')))
                    else:
                        print
                        print "Updating:", votedoc, rep, d['id'], fixvote(voter('vote'))
                        db.update('vote', where="bill_id=$d['id'] AND politician_id=$rep", vote=fixvote(voter('vote')),vars=locals())

        if not batch_mode: db.update('bill', where="id = $d['id']", yeas=yeas, neas=neas, vars=locals())
        d['yeas'] = yeas
        d['neas'] = neas
    if batch_mode: bill_list.append(d)


################################################################################
def main():
    from bulk_loader import bulk_loader_db
    for c,fn in enumerate(glob.glob(GOVTRACK_CRAWL+'/us/*/bills/*.xml')):
        loadbill(fn,batch_mode=True)


    db = bulk_loader_db(os.environ.get('WATCHDOG_TABLE', 'watchdog_dev'))
    bill_cols = ['id', 'session', 'type', 'number', 'introduced', 'title', 'sponsor', 'summary', 'maplightid', 'yeas', 'neas']
    db.open_table('bill', bill_cols, delete_first=True, filename=DATA_DIR+'load/bill.tsv')
    vote_col = ['bill_id', 'politician_id', 'vote']
    db.open_table('vote', vote_col, delete_first=True, filename=DATA_DIR+'load/vote.tsv')
    for bill in bill_list:
        db.insert('bill',**bill)
    for vote in vote_list.values():
        db.insert('vote',**vote)


if __name__ == "__main__":
    main()

    
