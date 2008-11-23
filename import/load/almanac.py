#!/usr/bin/python
import glob, web, os, cgitb, sys
import tools
from settings import db
from parse import almanac
sys.excepthook = cgitb.Hook(format='text', file=sys.stderr)
from pprint import pprint, pformat

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

def load_election_results(d, distname):
    (year, votes, vote_pct) = (0,'0','0')
    if 'name' not in d: 
        print "No name for the congress person for: ",distname
        return
    pname = d['name'].lower()
    if 'electionresults' not in d: 
        print "No election results for %s repsenting %s." % (d['name'],distname)
        return
    for e in d['electionresults']:
        if 'candidate' in e and 'primary' not in e['election'] and \
                pname.replace(' ','') in e['candidate'].lower().replace(' ',''):
            if int(e['election'][0:4]) > year: 
                (year,votes) = (int(e['election'][0:4]), e['totalvotes'])
                if 'percent' in e: vote_pct = e['percent']
    #print year, votes, vote_pct, d['name'], distname
    if year:
        pol=db.select('politician', what='id', 
                where="district_id='"+distname+"' AND "+web.sqlors('lastname ilike ',pname.split(' ')),
                vars=locals()).list()
        if pol and len(pol)==1: 
            polid=pol[0].id
            db.update('politician', where='id=$polid', 
                    n_vote_received=votes.replace(',','').replace('Unopposed','0'),
                    pct_vote_received=vote_pct.replace('%',''), 
                    last_elected_year=year, vars=locals());
        else: print "Couldn't find an id for %s representing %s." % (d['name'], distname)
    else: print "Didn't find a recent election for %s representing %s." %(d['name'], distname) #, pformat(d['electionresults'])

def demog_to_dist(demog, district):
    if demog:
        district.cook_index = get_int(demog, 'Cook Partisan Voting Index')
        district.area_sqmi = cleanint(web.rstrips(web.rstrips(demog['Area size'], ' sq. mi.'), ' square miles'))
        district.poverty_pct = get_int(demog, 'Poverty status') or get_int(demog, 'Poverty status') 
        district.median_income = get_int(demog, 'Median income') or get_int(demog, 'Median Income') 
        (district.est_population_year,
         district.est_population) = coalesce_population(demog, [
            (2006, 'Pop. 2006 (est)'),
            (2005, 'Pop. 2005 (est)'),
            (2000, 'Pop. 2000'),
            (2006, 'Population 2006 (est)'),
            (2005, 'Population 2005 (est)'),
            (2000, 'Population 2000'),
        ])


def main():
    assert os.path.exists(ALMANAC_DIR), ALMANAC_DIR
    
    files = glob.glob(ALMANAC_DIR + 'people/*/rep_*.htm') + \
            glob.glob(ALMANAC_DIR + 'people/*/*s[12].htm')
    files.sort()
    for fn in files:
        district = web.storage()
        demog = None
        
        dist = web.lstrips(web.rstrips(fn.split('/')[-1], '.htm'), 'rep_')
        diststate = dist[0:2].upper()
        distnum = dist[-2:]
        distname = tools.fixdist(diststate + '-' + distnum)
        
        d = almanac.scrape_person(fn)
        load_election_results(d, distname)

        if 'demographics' in d:
            demog = d['demographics']
        elif distname[-2:] == '00' or '-' not in distname:   # if -00 then this district is the same as the state.
            #print "Using state file for:", distname
            statefile = ALMANAC_DIR + 'states/%s/index.html' % diststate.lower()
            demog = almanac.scrape_state(statefile).get('state')

        demog_to_dist(demog, district)

        district.almanac = 'http://' + d['filename'][d['filename'].find('nationaljournal.com'):]

        #print 'district:', distname, pformat(district)
        db.update('district', where='name=$distname', vars=locals(), **district)

if __name__ == '__main__': main()
