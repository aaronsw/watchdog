"""
FEC data loader.
"""
from __future__ import with_statement
import itertools
import tools
from tools import db
from parse import fec

fec2pol = {}
def load_fec_ids():
    with db.transaction():
        db.delete('politician_fec_ids', '1=1')
        fh = iter(file('../data/crawl/opensecrets/FEC_CRP_ID.tsv'))
        header = fh.next()
        for line in fh:
            fec_id, crp_id = line.split()
            if tools.opensecretsp(crp_id):
                fec2pol[fec_id] = tools.opensecretsp(crp_id)
                db.insert('politician_fec_ids',
                  seqname=False,
                  politician_id=tools.opensecretsp(crp_id),
                  fec_id=fec_id)

def load_fec_cans():
    for can in fec.parse_candidates():
        if can.candidate_id in fec2pol:
            pol_id = fec2pol[can.candidate_id]
            
            total = float(can.total_receipts)
            if total == 0.0: 
                print "Oops:", pol_id, total, can.total_receipts, can.total_disbursements, can.contrib_from_candidate, can.total_indiv_contrib, can.contrib_from_other_pc
                continue
            db.update('politician', where='id = $pol_id', vars=locals(), 
              money_raised = can.total_receipts,
              pct_spent = can.total_disbursements/total,
              pct_self = can.contrib_from_candidate/total,
              pct_indiv = can.total_indiv_contrib/total,
              pct_pac = can.contrib_from_other_pc/total
            )

if __name__ == "__main__":
    load_fec_ids()
    load_fec_cans()
