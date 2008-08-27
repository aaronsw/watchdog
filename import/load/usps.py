"""
Load USPS data.
"""
from __future__ import with_statement
import gzip
from settings import db

#with db.transaction():
#db.delete('zip', '1=1')
allzips = set()
for line in file('../data/parse/all5digitzip.txt'):
    city, statezip = line.split(',')
    state, zip = statezip.split()
    allzips.add(zip)
#    db.insert('zip', seqname=False, city=city, state=state, zip=zip)

#db.delete('zip4', '1=1')
fho = file('zip4.tsv', 'w')
for line in gzip.open('../data/parse/zip4dist.txt.gz'):
    zip4, dist = line.split()
    zip5, plus4 = zip4.split('-')
    if plus4.endswith('ND'): continue
    if dist[:2] in [
      'AE', 'AA', 'AP', # Armed Forces
      'PW', # Palau
      'MP', # Marshall Islan
      'FM', # Federated States of Micronesia
      'VI', # Virgin Islands
    ]: continue
    
    if zip4 in ['22309-9501', '22309-9502', '22309-9503', '22309-9504'] and \
       dist != 'VA-11': continue
    if dist.endswith('99'):
        #@@ nebraska weirdness
        dist = dist[:-2] + '02'
    
    if zip5 not in allzips:
        print 'badzip', line
    
    fho.write('%s\t%s\t%s\n' % (zip5, plus4, dist))
    
    #try:
    #    db.insert('zip4', seqname=False, zip=zip, plus4=plus4, district=dist)
    #except Exception, e:
    #    print line
    #    print e
