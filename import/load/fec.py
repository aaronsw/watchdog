"""
FEC data loader.
"""
from __future__ import with_statement
import itertools
import web
import tools
from tools import db
from parse import fec_cobol, fec_csv

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
    for can in fec_cobol.parse_cansum():
        can = web.storage(can)
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

def load_fec_efilings():
    for f in fec_csv.parse_efilings():
        for s in f['schedules']:
            if s['type'] == 'contribution':
                politician_id = None
                if f['candidate_fec_id']:
                    fec_id = f['candidate_fec_id']
                    pol_fec_id = list(db.select('politician_fec_ids', where='fec_id=$fec_id', vars=locals()))
                    if pol_fec_id and len(pol_fec_id) == 1:
                        politician_id = pol_fec_id[0].politician_id
                elif not politician_id and f['candidate']:
                    names = f['candidate'].split(' ')
                    fn, ln = names[0], names[-1]
                    pol = list(db.select('politician', where='lastname=$ln and firstname=$fn', vars=locals()))
                    if pol and len(pol) == 1:
                        politician_id = pol[0].id
                db.insert('contribution',
                          committee=f['committee'],
                          contrib_date=s['date'],
                          contributor_org=s['contributor_org'],
                          contributor=s['contributor'],
                          occupation=s['occupation'],
                          employer=s['employer'],
                          employer_stem=tools.stemcorpname(s['employer']),
                          candidate_name=f['candidate'],
                          filer_id=f['filer_id'],
                          report_id=f['report_id'],
                          amount=s['amount'])
            else:
                db.insert('expenditure',
                          candidate_name=f['candidate'],
                          committee=f['committee'],
                          expenditure_date=s['date'],
                          recipient=s['recipient'],
                          filer_id=f['filer_id'],
                          report_id=f['report_id'],
                          amount=s['amount'])


if __name__ == "__main__":
    load_fec_ids()
    load_fec_cans()
    load_fec_efilings()
