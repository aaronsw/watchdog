#!/usr/bin/python
import glob, web, os, cgitb, simplejson, sys
from parse import almanac
sys.excepthook = cgitb.Hook(format='text', file=sys.stderr)

DATA_DIR = '../data'
ALMANAC_DIR = DATA_DIR + '/crawl/almanac/nationaljournal.com/pubs/almanac/2008/'

def cleanint(n):
    for c in ', %$':
        n = n.replace(c, '')
    return n

def get_int(dict, key):
    return cleanint(dict.get(key, '')) or None

def main():
    districts = simplejson.load(file(DATA_DIR + '/parse/districts/index.json'))
    
    assert os.path.exists(ALMANAC_DIR), ALMANAC_DIR
    out = {}
    for fn in glob.glob(ALMANAC_DIR + 'people/*/rep*'):
        district = web.storage()
        
        dist = web.lstrips(web.rstrips(fn.split('/')[-1], '.htm'), 'rep_')
        diststate = dist[0:2].upper()
        distnum = dist[-2:]
        
        d = almanac.scrape1(fn)
        if 'demographics' in d:
            demog = d['demographics']
        else:
            statefile = ALMANAC_DIR + 'states/%s/index.html' % diststate.lower()
            demog = almanac.scrape1(statefile).get('state')

        if demog:
            district.cook_index = get_int(demog, 'Cook Partisan Voting Index')
            district.area_sqmi = cleanint(web.rstrips(demog['Area size'], ' sq. mi.'))
            district.poverty_pct = get_int(demog, 'Poverty status')
            district.median_income = get_int(demog, 'Median income')
            district.est_population_2005 = get_int(demog, 'Pop. 2005 (est)')
            if district.est_population_2005 is None:
                district.est_population_2005 = get_int(demog, 'Pop. 2006 (est)')

        district.almanac = 'http://' + d['filename'][d['filename'].find('nationaljournal.com'):]

        # Nationaljournal numbers districts of congressmen-at-large
        # and territorial delegates '01' in its URLs, but our
        # districts file numbers them '00'.
        if distnum == '01' and diststate + '-00' in districts:
            distnum = '00'
        out[diststate + '-' + distnum]  = district
    return out

if __name__ == '__main__':
    print simplejson.dumps(main(), indent=2, sort_keys=True)
