"""
parse data from govtrack maps

from: data/crawl/govtrack/gis/gmapdata/
"""
import re
import simplejson as json
from settings import db

DISTRICT_TABLE = 'load/manual/districts.json'
GMAPDATA = '../data/crawl/govtrack/gis/gmapdata'

r_center = re.compile(r'map\.setCenter\(new GLatLng\(([-0-9.]+), ([-0-9.]+)\), (\d+)\);')

def main():
    districts = json.load(file(DISTRICT_TABLE))
    for dist in districts.iterkeys():
        try:
            d = file(GMAPDATA + '/%s-marker.js' % dist.replace('-0', '').replace('-', '')).read()
            x = r_center.findall(d)[0]
            db.update('district', where='name=$dist', vars=locals(), 
              center_lat = x[0], center_lng = x[1], zoom_level=x[2])
        except IOError: # file not found
            continue
    
if __name__ == "__main__": main()