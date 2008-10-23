#TODO:
#   - Detect dups in PAC table (capitalization, 'PAC' suffix, etc.)
#   - Improve schema... need to figure out how we're to use this first.
#   - Stable IDs for tables.
from __future__ import with_statement
import re
from pprint import pprint, pformat

import web

from settings import db
from parse import lobbyists


lob_organization =  {
    'organizationName': 'name',
}

lob_pac = {
    'name': 'name'
}

lob_person = {
    'lobbyistPrefix': 'prefix',
    'lobbyistFirstName': 'firstname',
    'lobbyistMiddleName': 'middlename',
    'lobbyistLastName': 'lastname',
    'lobbyistSuffix': 'suffix',
    'contactName': 'contact_name',
}

lob_filing = {
    'senateRegID': 'senate_id',
    'houseRegID': 'house_id',

    'filerType': 'filer_type',

    'reportYear': 'year',
    'reportType': 'type',
    'amendment': 'amendment',
    'signedDate': 'signed_date',
    'certifiedcontent': 'certified',
    #'noContributions': None,
    'comments': 'comments',
}

lob_contribution = {
    'type': 'type',
    'contributorName': 'contributor',
    'payeeName': 'payee',
    'recipientName': 'recipient',
    'amount': 'amount',
    'date': 'date' 
}

def load_house_lobbyists():
    print "Loading new lobbyist data."
    pac_id=[1]
    for i, x in enumerate(lobbyists.parse_house_lobbyists()):
        (per, org, fil) = ({}, {}, {})
        #pprint(x)
        for z, val in x.items():
            if z in lob_person: per[lob_person[z]] = val
            if z in lob_organization: org[lob_organization[z]] = val
            if z in lob_filing: fil[lob_filing[z]] = val

        # lob_person table
        if per:
            person = db.select('lob_person', where=web.db.sqlwhere(per,' AND '))
            per['id'] = i #@@ stable ids
            if not person:
                db.insert('lob_person', seqname=False, **per)
            else:
                per = person[0]

        # lob_organization table
        organization = db.select('lob_organization', where=web.db.sqlwhere(org,' AND '))
        org['id'] = i #@@ stable ids
        if not organization:
            db.insert('lob_organization', seqname=False, **org)
        else: 
            org = organization[0]

        # lob_filing table
        fil['lobbyist_id'] = per['id'] if 'id' in per else None
        fil['org_id'] = org['id']
        fil['id'] = x['file_id']
        db.insert('lob_filing', seqname=False, **fil)

        # lob_contribution table
        def insert_contribution(con):
            c = {}
            for z, val in con.items():
                if z == 'amount': val = int(float(val))
                if z in lob_contribution: c[lob_contribution[z]] = val
            db.insert('lob_contribution', seqname=False, filing_id=x['file_id'], **c)
        if 'contributions' in x:
            if isinstance(x['contributions'], list):
                for con in x['contributions']:
                    insert_contribution(con)
            else: 
                insert_contribution(x['contributions'])

        # lob_pac table
        def insert_pac(pac):
            pac_id[0] += 1
            pa = {'id':pac_id[0]}  #@@ stable ids
            for z, val in pac.items():
                if z in lob_pac: pa[lob_pac[z]] = val
            db_pac = db.select('lob_pac', where='name='+web.sqlquote(pa['name']))
            if not db_pac:
                db.insert('lob_pac', seqname=False, **pa)
            else:
                pa = db_pac[0]
            db.insert('lob_pac_filings',seqname=False, pac_id=pa['id'], filing_id=fil['id'])
        if 'pacs' in x:
            if isinstance(x['pacs'], list):
                for pac in x['pacs']:
                    insert_pac(pac)
            else: 
                insert_pac(x['pacs'])


if __name__ == "__main__":
    with db.transaction():
        print "Deleting old data from lob_* tables."
        db.delete('lob_pac_filings',where='1=1')
        db.delete('lob_contribution',where='1=1')
        db.delete('lob_filing',where='1=1')
        db.delete('lob_pac',where='1=1')
        db.delete('lob_person',where='1=1')
        db.delete('lob_organization',where='1=1')
        load_house_lobbyists()

