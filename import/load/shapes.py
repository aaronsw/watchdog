"""
load district shapes

from: data/crawl/census/cd99_110*.dat
  to: data/parse/districts/shapes.json
"""
import web
import simplejson

DATA_DIR = '../data/crawl/census'

def fips2state():
    out = {}
    states = simplejson.load(file('../data/load/states/index.json'))
    for stateid, state in states.iteritems():
        out[state['fipscode']] = stateid
    return out

def parse():
    states = fips2state()
    
    shapeid2district = {}
    for lines in web.group(file(DATA_DIR + '/cd99_110a.dat'), 7):
        num, fipscode, distnum, distname, distid, distdesc, ignore = [x.strip().strip('"') for x in lines]
        if not fipscode.strip(): continue
        shapeid2district[num] = states[fipscode] + '-' + distnum

    out = {}    
    for line in file(DATA_DIR + '/cd99_110.dat'):
        nums = line.strip().split()
        if len(nums) == 3:
            shapeid = nums[0] # other points are the center
            if shapeid in shapeid2district:
                SKIPME = False
                district = shapeid2district[shapeid]
                out.setdefault(district, [])
                out[district].append([])
            else:
                SKIPME = True
        elif len(nums) == 2 and not SKIPME:
            out[district][-1].append((float(nums[0]), float(nums[1])))

    return out

def load():
    """convert to GeoJSON"""
    out = {}
    for distid, polygons in parse().iteritems():
        out[distid] = {'outline': simplejson.dumps({'type': 'MultiPolygon', 'coordinates': polygons})}
    return simplejson.dumps(out, indent=2, sort_keys=True)

def tmp():
    shp = out['15']
    print 'var district_map_points = []'
    for (lng, lat) in shp:
        print 'district_map_points.push(new GLatLng(%s, %s))' % (lat, lng)

if __name__ == "__main__": print load()
