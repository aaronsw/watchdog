from __future__ import with_statement
from settings import db
import time

def generate_handshakes():
    print 'generating handshakes ...'
    pol2corp = db.query('SELECT es.politician_id as frm, '
                            'e.recipient_stem as to, '
                            'SUM(e.final_amt) as amount, '
                            '2008 as year ' #all the data is of 2008 as of now
                        'FROM earmark e, earmark_sponsor es '
                        'WHERE es.earmark_id = e.id and '
                        'e.recipient_stem is not null and '
                        "e.recipient_stem != '' "
                        'GROUP BY es.politician_id, e.recipient_stem, year')

    corp2pol = db.query('SELECT c.employer_stem as frm, '
                                'fec.politician_id as to, '
                                'SUM(c.amount) as amount, '
                                "date_part('year', sent) as year "
                        'FROM contribution c, committee pac, politician_fec_ids fec '
                        'WHERE c.recipient_id = pac.id and '
                        'pac.candidate_id = fec.fec_id and '
                        'c.employer_stem is not null and '
                        "c.employer_stem != '' "
                        'GROUP BY c.employer_stem, fec.politician_id, year')

    pols = {}
    for r in pol2corp:
        pols[r.to, r.frm, r.year] = r.amount
    
    corps = {}
    for r in corp2pol:
        corps[r.frm, r.to, r.year] = r.amount
    
    for k in pols:
        if k in corps:
            corp, pol, year = k
            yield dict(politician_id=pol, corporation=corp, year=year,  
                        pol2corp=pols[k], corp2pol=corps[k])

def load_handshakes(handshakes):
    with db.transaction():
        db.delete('handshakes', '1=1')
        for h in handshakes:
            db.insert('handshakes', seqname=False, **h)            
    
if __name__ == '__main__':
    load_handshakes(generate_handshakes())
