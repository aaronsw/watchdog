import simplejson
from settings import db

wyr = simplejson.load(file('../data/crawl/votesmart/wyr.json'))

types = dict(email='E', wyr='W', ima='I', zipauth='Z')

def load_wyr():
    for distname, data in wyr.iteritems():
            if data['contacttype'] == 'wyr':
                contact = 'https://forms.house.gov/wyr/welcome.shtml'
            else:
                contact = data['contact']    
                
            d = {'district':distname, 
                    'contact':contact,
                    'contacttype': types[data['contacttype']],
                    'captcha': data['captcha']
                   }
            db.insert('wyr', seqname=False, **d)
           
if __name__ == "__main__": 
    load_wyr()
