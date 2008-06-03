"""
load maplight info

from: data/crawl/maplight/
"""

from __future__ import with_statement

import csv
from tools import db
import bills
    
def load_data():
    c = csv.reader(file('../data/crawl/maplight/uniq_map_export_bill_research.csv'))
    supportdict = {'0': -1, '1': 1, '2': 0 } #0: oppose ; 1: support; 2: not known (from README)
    
    with db.transaction():
        db.delete('interest_group_bill_support', '1=1')
        for line in c:
            if not line[0].startswith('#'):
                category_id, longname, maplightid, session, measure, support = line
                support = supportdict[support]
                typenumber = measure.lower().replace(' ', '')
                    
                r = db.select('interest_group', what="id", where="longname=$longname", vars=locals())
                if r:
                    groupid = r[0].id
                else:
                    groupid = db.insert('interest_group', longname=longname, category_id=category_id)
                    
                bill_id = 'us/%s/%s' % (session, typenumber)
                r = db.select('bill', where="id=$bill_id", vars=locals())
                if not r:
                    filename = "../data/crawl/govtrack/us/%s/bills/%s.xml" % (session, typenumber)
                    bills.loadbill(filename, maplightid=maplightid)
                    
                try:
                    #print '\r', bill_id,
                    db.insert('interest_group_bill_support', seqname=False, bill_id=bill_id, group_id=groupid, support=support)
                except:
                    print '\n Duplicate row with billid %s groupid %s support %s longname %s' % (bill_id, groupid, support, longname)
                    raise
       
def load_categories():
    c = csv.reader(file('../data/crawl/maplight/CRP_Categories.csv'))
    with db.transaction():
        db.delete('category', '1=1')
        for line in c:
            if not line[0].startswith('#'):
                cid, cname, industry, sector, empty = line
                db.insert('category', seqname=False, id=cid, name=cname, industry=industry, sector=sector)
                  
def generate_similarities():
    """
    Generate similarity information for each (interest group, politician) pair and store in DB
    """
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
        db.delete('group_politician_similarity', '1=1')
        for k, agreed in sim.items():
            group_id, politician_id = k
            db.insert('group_politician_similarity', seqname=False, 
                group_id=group_id, politician_id=politician_id, agreed=agreed, total=total[k])
                
                                                                        
def aggregate_similarities():
    """
    Aggregate the similarity info in group_politician_similarity table, category wise. 
    """
    result = db.query("select sum(sim.agreed) as agreed, sum(sim.total) as total,"
                      " sim.politician_id, cat.name as category_name" 
                      " from group_politician_similarity sim, interest_group grp, category cat"
                      " where sim.group_id=grp.id and grp.category_id != '' and cat.id = grp.category_id"
                      " group by sim.politician_id, cat.name")    
    #for r in result:    
    #    print r.politician_id, r.category_name, r['agreed']*100.0/r['total'], r['agreed'], r['total']
    return result
         
def main():
    load_categories()
    load_data()
    generate_similarities()
    aggregate_similarities()
                                     
if __name__ == "__main__":
    main()
