"""
Load Project Vote Smart data.
"""
from __future__ import with_statement

from parse import votesmart
import json
import tools
from settings import db
import schema


def unidecode(d):
    newd = {}
    for k, v in d.iteritems():
        newd[k.encode('utf8')] = v
    return newd

# Mappings from votesmart to schema
cand_mapping = {
  'candidateId':'votesmartid',
  'electionParties':'party',
  'firstName':'firstname',
  'lastName':'lastname',
  'middleName':'middlename',
  'nickName':'nickname',
  'electionStatus' : 'election_status',
}
bios_mapping = {
  'firstName':'firstname',
  'lastName':'lastname',
  'middleName':'middlename',
  'nickName':'nickname',
  'gender':'gender',
  'birthDate':'birthday',
  'education':'education',
  'religion':'religion',
}

def filter_dict(f, d):
    if isinstance(f, dict):
        return dict([(i, d[k]) for k,i in f.items()])
    elif isinstance(f, list):
        return dict([(x, d[x]) for x in d.keys() if x in f])


from gen_ids import get_wd_id_VS as get_wd_id
def load_votesmart():
    # Candidates from votesmart
    for district, cands in votesmart.candidates():
        district=tools.fix_district_name(district)
        for pol in cands:
            vs_id=pol['candidateId']
            wd = get_wd_id(vs_id)
            if not wd: continue
            polid = wd['watchdog_id']

            pol_cand = filter_dict(cand_mapping, pol)
            if not db.select('politician', 
                    where='id=$polid', vars=locals()):
                db.insert('politician', 
                        seqname=False, 
                        id=polid, 
                        **unidecode(filter_dict(schema.Politician.columns.keys(),
                            pol_cand)))
            else:
                # @@ Should probably check that we really want to do this, but
                # it apears as though the data has two entries for current
                # members (the second having more info filled out).
                db.update('politician', where='id=$polid', vars=locals(),
                        **unidecode(filter_dict(schema.Politician.columns.keys(),
                            pol_cand)))

            if not db.select('congress',
                    where="politician_id=$polid AND congress_num='-1'", 
                    vars=locals()):
                db.insert('congress', seqname=False, congress_num='-1',
                        politician_id=polid, district_id=district,
                        party=pol_cand['party'])

    # Bios from votesmart
    for vs_id, p in votesmart.bios():
        pol = p['candidate']
        if pol['gender']:
            pol['gender']=pol['gender'][0]
        if pol['education']:
            pol['education'] = pol['education'].replace('\r\n', '\n')
        wd = get_wd_id(vs_id)
        if not wd: continue
        polid = wd['watchdog_id']
        pol_people = filter_dict(schema.Politician.columns.keys(),
                filter_dict(bios_mapping, pol))
        if db.select('politician', where='votesmartid=$vs_id',vars=locals()):
            db.update('politician', where='votesmartid=$vs_id', 
                    vars=locals(), **unidecode(pol_people))


def main():
    with db.transaction():
        db.update('politician', votesmartid=None, where='1=1')
        db.delete('congress', where="congress_num='-1'")
        load_votesmart()


if __name__ == "__main__": 
    main()


