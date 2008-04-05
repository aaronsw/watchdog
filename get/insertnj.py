import glob
import web
import scrapenj

db = web.database(dbn='postgres', db='watchdog_dev', user='postgres', pw='')
ALMANAC_DIR = 'almanac/nationaljournal.com/pubs/almanac/2008/people/'

for fn in glob.glob(ALMANAC_DIR + '*/rep*'):
    dist = web.lstrips(web.rstrips(fn.split('/')[-1], '.htm'), 'rep_')
    dist = dist[0:2].upper() + '-' + dist[-2:]
    
    d = scrapenj.scrape1(fn)
    if 'demographics' not in d: continue
    cook_index = d['demographics']['Cook Partisan Voting Index'].replace(' ', '')
    area_sqmi = d['demographics']['Area size']
    area_sqmi = web.rstrips(area_sqmi, ' sq. mi.').replace(',', '').replace(' ', '')
    
    db.insert('district', seqname=False, name=dist, state=dist[:2], district=dist[-2:], cook_index=cook_index, area_sqmi=area_sqmi)
