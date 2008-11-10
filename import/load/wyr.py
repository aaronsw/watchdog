from __future__ import with_statement
import simplejson as json
from settings import db

wyr = json.load(file('../data/crawl/votesmart/wyr.json'))

types = dict(email='E', wyr='W', ima='I', zipauth='Z')

def load_wyr():
    with db.transaction():
        db.delete('pol_contacts', where='1=1')
        for pol, data in wyr.iteritems():
                if data['contacttype'] not in types.keys(): 
                    continue

                if data['contacttype'] == 'wyr':
                    contact = 'https://forms.house.gov/wyr/welcome.shtml'
                else:
                    contact = data['contact']    
            
                d = {'politician_id':pol,
                        'contact':contact,
                        'contacttype': types[data['contacttype']],
                        'captcha': data['captcha']
                       }
                try:
                    db.insert('pol_contacts', seqname=False, **d)
                except:
                    continue
           
if __name__ == "__main__": 
    load_wyr()
