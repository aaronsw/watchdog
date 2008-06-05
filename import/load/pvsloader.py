#! /usr/bin/env python
'''
Project VoteSmart data loader
Created by Pradeep Gowda
2008.05.29
'''

from __future__ import with_statement
import os
import web
from BeautifulSoup import BeautifulSoup


db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'),
                  db='watchdog_dev')

soup = BeautifulSoup(open('../../data/crawl/govtrack/people.xml','r'))

people = soup.findAll('person')
print 'Done reading...'

cnt = 0 
with db.transaction():
    for person in people:
        vars = {}
        for k,v in person.attrs:
            vars[str(k)] = unicode(v)
            if v == '0000-00-00': 
                vars[str(k)] = None

        person_id = db.insert('person', seqname=False, **vars)
        roles = person.findAll('role')
        for role in roles:
            vars = {}
            for k,v in role.attrs:
                vars[str(k)] = unicode(v)
            vars['person_id'] = person_id
            prole_id = db.insert('prole', seqname='prole_serial', **vars)
            committees = role.findAll('current-committee-assignment')    
            if committees:
                for committee in committees:
                    vars = {}
                    for k,v in committee.attrs:
                        vars[str(k)] = unicode(v)
                    cmrole = vars.get('role')
                    if cmrole: vars.pop('role')
                    #check for existing record
                    try:
                        params = {'cmt':vars['committee'], 'subcmt': vars.get('subcommittee')}
                        committee_id = db.select('committee', where='committee=$cmt and subcommittee=$subcmt', **params)[0]
                    except:
                        committee_id = db.insert('committee', seqname='committee_serial', **vars)
                    vars = {}
                    vars['prole_id'] = prole_id
                    vars['committee_id'] = committee_id
                    vars['role'] = cmrole
                    committee_assignment_id = db.insert('committee_assignment', seqname='committee_assignment_serial', **vars)

        cnt += 1
        if cnt % 1000 == 0:
            print '... ',cnt

print 'DONE... ', cnt