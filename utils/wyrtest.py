import web
from settings import db
from writerep import writerep

def test(formtype=None):
    def getdistzipdict(zipdump):
        """returns a dict with district names as keys zipcodes falling in it as values"""
        d = {}
        for line in zipdump.strip().split('\n'):
            zip5, zip4, dist = line.split('\t')
            d[dist] = (zip5, zip4)
        return d

    try:        
       dist_zip_dict =  getdistzipdict(file('zip_per_dist.tsv').read())
    except:
       import os, sys
       path = os.path.dirname(sys.modules[__name__].__file__)
       dist_zip_dict =  getdistzipdict(file(path + '/zip_per_dist.tsv').read())

    def getzip(dist):
        return dist_zip_dict[dist]
          
          
    query = "select district from politician, pol_contacts" 
    query += " where pol_contacts.politician = politician.id " 
    if formtype == 'wyr':  query += "and contacttype='W'"
    elif formtype == 'ima': query += "and contacttype='I'"
    elif formtype == 'zipauth': query += "and contacttype='Z'"
    elif formtype =='email': query += "and contacttype='E'"
    
    dists = [r.district for r in db.query(query + ' limit 2')]
    for dist in dists:
        print dist,        
        zip5, zip4 = getzip(dist)
        msg_sent = writerep(dist, zipcode=zip5, zip4=zip4, prefix='Mr.', 
                    fname='watchdog', lname ='Tester', addr1='111 av', addr2='addr extn', city='test city', 
                    phone='001-001-001', email='test@watchdog.net', subject='general', msg='testing...')
        print msg_sent and 'Success' or 'Failure'
    
if __name__ == '__main__':
    test('email')
    test('wyr')
    test('ima')
    test('zipauth')
