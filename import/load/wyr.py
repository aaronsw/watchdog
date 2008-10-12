from __future__ import with_statement
import simplejson as json
from settings import db

wyr = json.load(file('../data/crawl/votesmart/wyr.json'))

types = dict(email='E', wyr='W', ima='I', zipauth='Z')

def load_wyr():
    with db.transaction():
        db.delete('pol_contacts', where='1=1')
        for distname, data in wyr.iteritems():
                if data['contacttype'] not in types.keys(): 
                    continue

                if data['contacttype'] == 'wyr':
                    contact = 'https://forms.house.gov/wyr/welcome.shtml'
                else:
                    contact = data['contact']    
            
                pol = db.select('politician', what='id', where='district_id=$distname', vars=locals())[0].id
                d = {'politician':pol, 
                        'contact':contact,
                        'contacttype': types[data['contacttype']],
                        'captcha': data['captcha']
                       }
                   
                db.insert('pol_contacts', seqname=False, **d)
           
if __name__ == "__main__": 
    load_wyr()
