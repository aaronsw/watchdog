"""
parse district shapes

from: data/crawl/census/cd99_110*.dat
"""
import web
import tools

DATA_DIR = '../data/crawl/census'

def parse():
    shapeid2district = {}
    for filename,grp in [('cd99_110',7), ('st99_d00',6)]:
        for lines in web.group(file(DATA_DIR + '/'+filename+'a.dat'), grp):
            if filename[0:2] == 'cd':
                num, fipscode, distnum, distname, distid, distdesc, ignore = \
                        [x.strip().strip('"') for x in lines]
            elif filename[0:2] == 'st':
                num, fipscode, distname, distdesc, ignore, ignore2 = \
                        [x.strip().strip('"') for x in lines]
                distnum = None
            if not fipscode.strip(): continue
            shapeid2district[num] = (fipscode, distnum)
        
        out = {}
        for line in file(DATA_DIR + '/'+filename+'.dat'):
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
