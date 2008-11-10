import web
from settings import db
from writerep import writerep
from wyrutils import pol2dist

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
        try:
            return dist_zip_dict[dist]
        except KeyError:
            for d in dist_zip_dict.keys():
                if d.startswith(dist+'-'):
                    return dist_zip_dict[d]
        return '', ''
          
          
    query = "select politician_id from pol_contacts where contacttype='%s'" % formtype[0].upper() 
    pols = [r.politician_id for r in db.query(query)]
    for pol in pols:
        print pol,        
        zip5, zip4 = getzip(pol2dist(pol))
        print zip5, zip4,
        try:
            msg_sent = writerep(pol, zipcode=zip5, zip4=zip4, prefix='Mr.', 
                    fname='watchdog', lname ='Tester', addr1='111 av', addr2='addr extn', city='test city', 
                    phone='0010010010', email='test@tryitout.net', subject='general', msg='testing...')
        except Exception, details:
            print details,
            msg_sent = False            
        print msg_sent and 'Success' or 'Failure'
    
if __name__ == '__main__':
    test('email')
    test('wyr')
    test('ima')
    test('zipauth')
