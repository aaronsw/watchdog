#!/usr/bin/python
import glob, web, os, cgitb, simplejson, sys
import tools
from settings import db
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

def coalesce_population(data, fields):
    for year, key in fields:
        pop = get_int(data, key)
        if pop is not None: return (year, pop)
    return (None, None)

def main():
    assert os.path.exists(ALMANAC_DIR), ALMANAC_DIR
    
    for fn in glob.glob(ALMANAC_DIR + 'people/*/rep*.htm'):
        district = web.storage()
        
        dist = web.lstrips(web.rstrips(fn.split('/')[-1], '.htm'), 'rep_')
        diststate = dist[0:2].upper()
        distnum = dist[-2:]
        
        d = almanac.scrape_person(fn)
        if 'demographics' in d:
            demog = d['demographics']
        else:
            #@@ maybe only when ends with '-00'?
            statefile = ALMANAC_DIR + 'states/%s/index.html' % diststate.lower()
            demog = almanac.scrape_state(statefile).get('state')

        if demog:
            district.cook_index = get_int(demog, 'Cook Partisan Voting Index')
            district.area_sqmi = cleanint(web.rstrips(demog['Area size'], ' sq. mi.'))
            district.poverty_pct = get_int(demog, 'Poverty status')
            district.median_income = get_int(demog, 'Median income')
            (district.est_population_year,
             district.est_population) = coalesce_population(demog, [
                (2006, 'Pop. 2006 (est)'),
                (2005, 'Pop. 2005 (est)'),
                (2000, 'Pop. 2000'),
            ])

        district.almanac = 'http://' + d['filename'][d['filename'].find('nationaljournal.com'):]
        distname = tools.fixdist(diststate + '-' + distnum)
        
        db.update('district', where='name=$distname', vars=locals(), **district)

if __name__ == '__main__': main()
