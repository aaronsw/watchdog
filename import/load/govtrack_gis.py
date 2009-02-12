"""
parse data from govtrack maps

from: data/crawl/govtrack/gis/gmapdata/
"""
import re
import simplejson as json
from settings import db
from pprint import pprint
from glob import glob

STATE_TABLE = 'load/manual/states.json'
DISTRICT_TABLE = 'load/manual/districts.json'
GMAPDATA = '../data/crawl/govtrack/gis/gmapdata'

r_center = re.compile(r'map\.setCenter\(new GLatLng\(([-0-9.]+), ([-0-9.]+)\), (\d+)\);')

def main():
    districts = json.load(file(DISTRICT_TABLE))
    states = json.load(file(STATE_TABLE))
    for table in [districts, states]:
        for dist in table.iterkeys():
            dname = GMAPDATA + '/%s[_-]marker*.js' % dist.replace('-0', '').replace('-', '')
            dname = glob(dname)
            if not dname: continue # File not found
            dname = dname[0]
            d = file(dname).read()
            x = r_center.findall(d)[0]
            db.update('district', where='name=$dist', vars=locals(), 
              center_lat = x[0], center_lng = x[1], zoom_level=x[2])
    
if __name__ == "__main__": main()
