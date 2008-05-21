"""
load maplight info

from: data/crawl/maplight/
"""

from __future__ import with_statement

import csv
from tools import db
import bills
    
def loaddata():
    c = csv.reader(file('../data/crawl/maplight/uniq_map_export_bill_research.csv'))
    supportdict = {'0': -1, '1': 1, '2': 0 } #0: oppose ; 1: support; 2: not known (from README)
    
    with db.transaction():
        for line in c:
            if not line[0].startswith('#'):
                group_id, longname, maplightid, session, measure, support = line
                support = supportdict[support]
                typenumber = measure.lower().replace(' ', '')
                    
                r = db.select('interest_group', what="id", where="longname=$longname", vars=locals())
                if r:
                    groupid = r[0].id
                else:
                    groupid = db.insert('interest_group', longname=longname)
                    
                bill_id = 'us/%s/%s' % (session, typenumber)
                r = db.select('bill', where="id=$bill_id", vars=locals())
                if not r:
                    filename = "../data/crawl/govtrack/us/%s/bills/%s.xml" % (session, typenumber)
                    bills.loadbill(filename, maplightid=maplightid)
                    
                try:
                    db.insert('interest_group_bill_support', seqname=False, bill_id=bill_id, group_id=groupid, support=support)
                except:
                    print '\n Duplicate row with billid %s groupid %s support %s longname %s' % (bill_id, groupid, support, longname)
                    raise
                  
def generate_similarities():
    result = db.query('select igbp.group_id, vote.politician_id, igbp.support, vote.vote'
                    ' from interest_group_bill_support igbp, vote'
                    ' where igbp.bill_id = vote.bill_id')
    sim = {}
    total = {}
             
    for r in result:
        k = (r.group_id, r.politician_id)
        if r.support == r.vote and r.support != 0:
            sim[k] = sim.get(k, 0) + 1
        total[k] = total.get(k, 0) + 1
    
    with db.transaction():
        for k, agreed in sim.items():
            group_id, politician_id = k
            db.insert('group_politician_similarity', seqname=False, 
                group_id=group_id, politician_id=politician_id, agreed=agreed, total=total[k])
                                            
if __name__ == "__main__":
    loaddata()
    generate_similarities()
