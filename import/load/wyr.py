import simplejson
from settings import db

wyr = simplejson.load(file('../data/crawl/wyr.json'))

def load_wyr():
    for distname, data in wyr.iteritems():
            vars = {'district':distname, 
                    'wyrform':data['wyrform'],
                    'captcha': data['captcha'],
                    'contactform': data['contactform'],
                    'imaissue': data['ima'],
                    'zipauth': data['zipauth']
                   }
            db.insert('wyr', seqname=False, **vars)
           
if __name__ == "__main__": 
    load_wyr()
