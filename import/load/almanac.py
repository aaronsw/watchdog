#!/usr/bin/python
import glob, web, os, cgitb
import simplejson
from parse import almanac

DATA_DIR = '../data'
ALMANAC_DIR = DATA_DIR + '/crawl/almanac/nationaljournal.com/pubs/almanac/2008/people/'

def cleanint(n):
    for c in ', %$':
        n = n.replace(c, '')
    return n

def main():
    districts = simplejson.load(file(DATA_DIR + '/parse/districts/index.json'))
    
    assert os.path.exists(ALMANAC_DIR), ALMANAC_DIR
    out = {}
    for fn in glob.glob(ALMANAC_DIR + '*/rep*'):
        district = web.storage()
        
        dist = web.lstrips(web.rstrips(fn.split('/')[-1], '.htm'), 'rep_')
        
        d = almanac.scrape1(fn)
        if 'demographics' in d:
            demo = d['demographics']
            district.cook_index = cleanint(demo['Cook Partisan Voting Index'])
            district.area_sqmi = cleanint(web.rstrips(demo['Area size'], ' sq. mi.'))
            district.poverty_pct = cleanint(demo['Poverty status'])
            district.median_income = cleanint(demo['Median income'])
            if 'Pop. 2005 (est)' in demo and cleanint(demo['Pop. 2005 (est)']):
                district.est_population_2005 = cleanint(demo['Pop. 2005 (est)'])
        district.njfilename = 'file://%s/%s' % (os.getcwd(), d['filename'])
        
        diststate = dist[0:2].upper()
        distnum = dist[-2:]
        if distnum == '01' and diststate + '-00' in districts:
            distnum = '00'
        out[diststate + '-' + distnum]  = district
    return out

if __name__ == '__main__':
    print simplejson.dumps(main(), indent=2, sort_keys=True)
