#!/usr/bin/python
import glob, web, scrapenj, os

db = web.database(dbn='postgres', db='watchdog_dev', user='postgres', pw='')
ALMANAC_DIR = 'almanac/nationaljournal.com/pubs/almanac/2008/people/'

def cleanint(n):
    for c in ', %$':
        n = n.replace(c, '')
    return n

def main():
    assert os.path.exists(ALMANAC_DIR), ALMANAC_DIR
    for fn in glob.glob(ALMANAC_DIR + '*/rep*'):
        district = web.storage()

        dist = web.lstrips(web.rstrips(fn.split('/')[-1], '.htm'), 'rep_')
        district.state = dist[0:2].upper()
        district.district = dist[-2:]
        district.name = district.state + '-' + district.district

        d = scrapenj.scrape1(fn)
        if 'demographics' in d:
            demo = d['demographics']
            district.cook_index = cleanint(demo['Cook Partisan Voting Index'])
            district.area_sqmi = cleanint(web.rstrips(demo['Area size'], ' sq. mi.'))
            district.poverty_pct = cleanint(demo['Poverty status'])
            district.median_income = cleanint(demo['Median income'])

        db.insert('district', seqname=False, **district)

if __name__ == '__main__': main()
