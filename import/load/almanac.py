#!/usr/bin/python
from __future__ import with_statement
import glob, web, os, cgitb, sys
import tools
from settings import db
from parse import almanac
sys.excepthook = cgitb.Hook(format='text', file=sys.stderr)

DATA_DIR = '../data'
ALMANAC_DIR = DATA_DIR + '/crawl/almanac/nationaljournal.com/pubs/almanac/'

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

def load_into_db(pname, distname, electionresults, recent_election_year):
    pol=db.select('politician', what='id',
            where="district_id=$distname AND %s" % web.sqlors('lastname ilike ', pname.split(' ')),
            vars=locals()).list()
    if len(pol) != 1:
        print "Couldn't find an id for %s representing %s." % (pname, distname)
        return
        
    polid=pol[0].id
    with db.transaction():
        for r in electionresults:
            if r.year == recent_election_year and r.type == 'Gen':
                db.update('politician', where='id=$polid', 
                    n_vote_received=r.votes,
                    pct_vote_received=r.vote_pct,
                    last_elected_year=r.year, vars=locals())
            db.insert('past_elections', seqname=False, politician_id=polid, district_id=distname,
                    votes_received=r.votes, pct_votes_received=r.vote_pct, type=r.type,
                    year=r.year, expenditure=r.expenditure)

def validate(d, distname):
    if 'name' not in d:
        print "No name for the congress person for: ", distname
    elif 'electionresults' not in d: 
        print "No election results for %s repsenting %s." % (d['name'], distname)
    else:
        return d

def process(d):
    election_results = []
    pname = d['name'].lower()
    for e in d['electionresults']:
        if 'candidate' in e and 'primary' not in e['election'] and \
               pname.replace(' ','') in e['candidate'].lower().replace(' ',''):
            r = web.storage(candidate=e['candidate'])
            r.year =  int(e['election'][0:4])
            r.votes = e['totalvotes'].replace(',','').replace('Unopposed','0')
            r.vote_pct = 100 if e['totalvotes'] == 'Unopposed' else e['percent'].replace('%', '')
            r.expenditure = e.get('expenditures', '0').lstrip('$').replace(',', '')
            r.type = 'SpGen' if 'special-general' in e['election'] else 'Gen'
            election_results.append(r)
    return election_results
    
def load_election_results(d, distname):    
    d = validate(d, distname)
    if not d: return
    pname = d['name'].lower()
    election_results = process(d)
    if not election_results:
        print "Didn't find a recent election for %s representing %s." %(d['name'], distname)
        return

    recent_election_year = max([e.year for e in election_results])
    load_into_db(pname, distname, election_results, recent_election_year)

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
    
    files = glob.glob(ALMANAC_DIR + '*/people/*/rep_*.htm') + \
            glob.glob(ALMANAC_DIR + '*/people/*/*s[12].htm')
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
