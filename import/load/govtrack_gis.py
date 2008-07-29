"""
parse data from govtrack maps

from: data/crawl/govtrack/gis/gmapdata/
to:   data/parse/districts/centers.js
"""
import re
import simplejson

r_center = re.compile(r'map\.setCenter\(new GLatLng\(([-0-9.]+), ([-0-9.]+)\), (\d+)\);')

def main():
    districts = simplejson.load(file('../data/load/districts/index.json'))
    out = {}
    for dist in districts.iterkeys():
        try:
            d = file('../data/crawl/govtrack/gis/gmapdata/%s-marker.js' % dist.replace('-0', '').replace('-', '')).read()
            x = r_center.findall(d)[0]
            out[dist] = {'center_lat': x[0], 'center_lng': x[1], 'zoom_level': x[2]}
        except IOError: # file not found
            continue
    return out
    
if __name__ == "__main__":
    print simplejson.dumps(main(), indent=2, sort_keys=True)
