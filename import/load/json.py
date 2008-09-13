import os, glob
import simplejson
import web
from settings import db
import cgitb
cgitb.enable(format='text')

DATA_DIR = 'load/manual'

def unidecode(d):
    newd = {}
    for k, v in d.iteritems():
        newd[k.encode('utf8')] = v
    return newd

def items(fname):
    print 'loading', fname
    return simplejson.load(file(DATA_DIR + '/%s.json' % fname)).iteritems()

def load_all():
    for code, state in items('states'):
        if 'aka' in state: state.pop('aka')
        db.insert('state', seqname=False, code=code, **unidecode(state))

    for name, district in items('districts'):
        db.insert('district', seqname=False, name=name, **unidecode(district))

    for polid, pol in items('politicians'):
        db.insert('politician', seqname=False, id=polid, wikipedia=pol.get('wikipedia'))

if __name__ == "__main__": load_all()
