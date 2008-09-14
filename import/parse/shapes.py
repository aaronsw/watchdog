"""
parse district shapes

from: data/crawl/census/cd99_110*.dat
"""
import web
import tools

DATA_DIR = '../data/crawl/census'

def parse():
    shapeid2district = {}
    for lines in web.group(file(DATA_DIR + '/cd99_110a.dat'), 7):
        num, fipscode, distnum, distname, distid, distdesc, ignore = \
          [x.strip().strip('"') for x in lines]
        if not fipscode.strip(): continue
        shapeid2district[num] = (fipscode, distnum)
    
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
    
    for (fipscode, distnum), shapes in out.iteritems():
        yield {
          '_type': 'district', 
          'state_fipscode': fipscode, 
          'district': distnum,
          'shapes': shapes
        }

if __name__ == "__main__": tools.export(parse())