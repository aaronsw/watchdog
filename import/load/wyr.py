import simplejson
from settings import db

wyr = simplejson.load(file('../data/crawl/votesmart/wyr.json'))
wyr_manual = simplejson.load(file('../data/crawl/votesmart/wyr_manual.json'))
wyr_manual.update(wyr)

types = dict(email='E', wyr='W', ima='I', zipauth='Z')

def load_wyr():
    for distname, data in wyr_manual.iteritems():
            if data['contacttype'] not in types.keys(): 
                continue

            if data['contacttype'] == 'wyr':
                contact = 'https://forms.house.gov/wyr/welcome.shtml'
            else:
                contact = data['contact']    
                
            d = {'district':distname, 
                    'contact':contact,
                    'contacttype': types[data['contacttype']],
                    'captcha': data['captcha']
                   }
                   
            db.insert('wyr3', seqname=False, **d)
           
if __name__ == "__main__": 
    load_wyr()
