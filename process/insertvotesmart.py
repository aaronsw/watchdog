#!/usr/bin/python
# Turn Aaron's crawl of the votesmart.org API data into SQL.
import pickle, cgitb, sys
cgitb.enable(format='text')

def escapechar(char):
    if char in "'\\": return "\\" + char
    else: return char
def sqlescape(astr):
    return "'%s'" % (''.join(escapechar(char) for char in astr))
def insert(table, contents):
    columns = contents.keys()
    fields = ', '.join(columns)
    values = ', '.join(sqlescape(contents[field]) for field in columns)
    return (u'insert into %s (%s) values (%s);' % (table, fields, values)
            ).encode('utf-8')
def create(table, fields):
    linesep = '\n    '
    sep = ',' + linesep
    return (u'create table %s (%s%s\n);' % (table, linesep, sep.join(
        '%s text' % field for field in fields
    ))).encode('utf-8')

files = {
    'districts': ['name', 'districtId', 'stateId', 'officeId'],
    'candidates': ['suffix', 'officeStateId', 'electionStatus',
                   'electionYear', 'officeDistrictId', 'electionDistrictId',
                   'candidateId', 'firstName', 'title', 'middleName',
                   'lastName', 'electionParties', 'electionStateId',
                   'nickName', 'officeParties'],
    'officials': ['suffix', 'officeStateId', 'electionStatus', 'electionYear',
                  'officeDistrictId', 'electionDistrictId', 'candidateId',
                  'firstName', 'title', 'middleName', 'lastName',
                  'electionParties', 'electionStateId', 'nickName',
                  'officeParties'],
}

def insert_from_pickle(fname, fo):
    for item in pickle.load(fo):
        if hasattr(item, 'keys'): print insert(fname, item)
        else: print "-- funky item: %r" % (item,)

def main():
    for fname in files.keys():
        print create(fname, files[fname])
        fo = file(fname + '.pkl')
        while 1: # loop in case there's more than one pickled graph per file
            try: insert_from_pickle(fname, fo)
            except EOFError: break
        print
if __name__ == '__main__': main()
