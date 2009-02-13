"""
FEC data loader.
"""
from __future__ import with_statement
import itertools, datetime
import web
import tools
from tools import db
from parse import fec_cobol, fec_csv, fec_crude_csv
import psycopg2 # @@sigh
import cgitb
import glob

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

def load_fec_committees():
    db.delete('contribution', '1=1')
    db.delete('committee', '1=1')
    for f in fec_cobol.parse_committees(reverse=True):
        f = web.storage(f)
        try:
            db.insert('committee', seqname=False,
              id = f.committee_id,
              name = f.committee_name,
              treasurer = f.treasurer_name,
              street1 = f.street_one,
              street2 = f.street_two,
              city = f.city,
              state = f.state,
              zip = f.zip,
              connected_org_name = f.connected_org_name,
              candidate_id = f.candidate_id,
              type = f.committee_type
            )
        except psycopg2.IntegrityError:
            pass # already imported

def load_fec_contributions():
    t = db.transaction(); n = 0
    db.delete('contribution', '1=1')
    for f in fec_cobol.parse_contributions():
        f = web.storage(f)
        f.occupation = f.occupation.replace('N/A', '')
        if '/' in f.occupation:
            employer, occupation = f.occupation.split('/', 1)
        else:
            employer = ''
            occupation = f.occupation
        
        try:
            datetime.date(*[int(x) for x in f.date.split('-')])
        except ValueError:
            f.date = None
        
        db.insert('contribution',
          fec_record_id = f.get('fec_record_id'),
          microfilm_loc = f.microfilm_loc,
          recipient_id = f.filer_id,
          name = f.name,
          street = f.get('street'),
          city = f.city,
          state = f.state,
          zip = f.zip,
          occupation = occupation,
          employer = employer,
          employer_stem = tools.stemcorpname(employer),
          committee = f.from_id or None,
          sent = f.date,
          amount = f.amount
        )
        n += 1
        if n % 10000 == 0: t.commit(); t = db.transaction(); print n
    t.commit()

def load_fec_efilings(filepattern=fec_crude_csv.DEFAULT_EFILINGS_FILEPATTERN):
    for f, schedules in fec_crude_csv.parse_efilings(glob.glob(filepattern)):
        for s in schedules:
            if s.get('type') == 'contribution':
                # XXX all this code for politician_id is currently
                # dead, does nothing useful
                politician_id = None
                if f.get('candidate_fec_id'):
                    fec_id = f['candidate_fec_id']
                    pol_fec_id = list(db.select('politician_fec_ids',
                                                where='fec_id=$fec_id',
                                                vars=locals()))
                    if pol_fec_id and len(pol_fec_id) == 1:
                        politician_id = pol_fec_id[0].politician_id
                elif not politician_id and f.get('candidate'):
                    names = f['candidate'].split(' ')
                    fn, ln = names[0], names[-1]
                    pol = list(db.select('politician',
                                        where='lastname=$ln and firstname=$fn',
                                        vars=locals()))
                    if pol and len(pol) == 1:
                        politician_id = pol[0].id
                db.insert('contribution',
                          committee=f['committee'],
                          contrib_date=s['date'],
                          contributor_org=s.get('contributor_org'),
                          contributor=s['contributor'],
                          occupation=s['occupation'],
                          employer=s['employer'],
                          employer_stem=tools.stemcorpname(s['employer']),
                          candidate_name=f.get('candidate'),
                          filer_id=f['filer_id'],
                          report_id=f['report_id'],
                          amount=s['amount'])
            elif s.get('type') == 'expenditure':
                db.insert('expenditure',
                          candidate_name=f.get('candidate'),
                          committee=f['committee'],
                          expenditure_date=s['date'],
                          recipient=s['recipient'],
                          filer_id=f['filer_id'],
                          report_id=f['report_id'],
                          amount=s['amount'])
            else:
                print "ignoring record of type %s" % \
                      s['original_data'].get('form_type')

def load_cans_fec_data():
    """Calculate percentage from business versus labor PACs
    Calculate percentage money within-state
    Calculate percentage money from small donors """
    for p in db.query("""SELECT id FROM politician"""):
        polid = p.id
        num = db.query("""SELECT count(*) 
                FROM committee cm, politician_fec_ids pfi, 
                politician p, contribution cn WHERE cn.recipient_id = cm.id 
                AND cm.candidate_id = pfi.fec_id AND pfi.politician_id = p.id 
                AND p.id = $polid""", vars=locals())[0].count
        if num:
            num_labor = db.query("""SELECT count(*) 
                FROM committee cm, politician_fec_ids pfi, politician p, contribution cn 
                WHERE cn.recipient_id = cm.id AND cm.candidate_id = pfi.fec_id 
                AND pfi.politician_id = p.id AND cm.type = 'L' 
                AND p.id = $polid""", vars=locals())[0].count
            labor_pct = num_labor/float(num)
            num_instate = db.query("""SELECT count(*) 
                FROM committee cm, politician_fec_ids pfi, politician p, 
                contribution cn, district d, state s
                WHERE cn.recipient_id = cm.id AND cm.candidate_id = pfi.fec_id 
                AND pfi.politician_id = p.id AND p.district_id = d.name 
                AND d.state_id = s.code AND lower(cn.state) = lower(s.code)
                AND p.id = $polid""", vars=locals())[0].count
            instate_pct = num_instate/float(num)
            num_smalldonor = db.query("""SELECT count(*) 
                FROM committee cm, politician_fec_ids pfi, politician p, contribution cn 
                WHERE cn.recipient_id = cm.id AND cm.candidate_id = pfi.fec_id 
                AND pfi.politician_id = p.id AND p.id = $polid 
                AND cn.amount < 250""", vars=locals())[0].count
            smalldonor_pct = num_smalldonor/float(num)
        else:
            labor_pct = 0
            instate_pct = 0
            smalldonor_pct = 0
        db.update('politician', where='id = $polid', vars=locals(),
          pct_labor = labor_pct,
          pct_instate = instate_pct,
          pct_smalldonor = smalldonor_pct
        )
        print polid, labor_pct, instate_pct, smalldonor_pct

if __name__ == "__main__":
    cgitb.enable(format='text')
    #load_fec_ids()
    #load_fec_cans()
    #load_fec_committees()
    #load_fec_contributions()
    #load_fec_efilings()
    load_cans_fec_data()
