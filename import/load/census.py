from __future__ import with_statement
import os, sys
from pprint import pprint, pformat

import web

from parse import census

batch_mode = True
DATA_DIR='../data/'
tsv_file_format = DATA_DIR+'load/%s.tsv'


def load_census_meta(type):
    print >>sys.stderr, "Loading census_meta table..."
    str_cols = set(['FILEID', 'STUSAB', 'CHARITER', 'CIFSN', 'LOGRECNO',])
    all_keys = {}
    # Build list
    labelMap = {}
    for table in census.ALL_TABLES[type]:
        (_,lm,pathMap) = census.parse_sas_file(type, table, all_keys)
        labelMap.update(lm)

    # Now insert
    for hr_key, int_keys in all_keys.items():
        for k in int_keys:
            if k in str_cols: continue
            db.insert('census_meta', 
                    seqname=False,
                    internal_key=k,
                    census_type=type,
                    label=labelMap[k].replace('\t','    '),
                    hr_key=hr_key)
    print >>sys.stderr, "...Done loading census_meta table."


def load_census_population():
    print >>sys.stderr, "Loading census_population table..."
    #db.delete('census_population', where='1=1')
    geoTables = {}
    # Load the population data from SF101.
    required_geo_keys = set(['LOGRECNO', 'SUMLEV', 'STATE', 'CD110', 'COUNTY',
        'BLKGRP', 'BLOCK', 'TRACT', 'ZCTA5', 'AREALAND'])
    desired_sumlevs = set(['STATE', 'COUNTY', 'DISTS', 'ZCTA', 'TRACT',
        'BLOCK'])
    for row in census.parse_state_sum_files([1], ['P002001']):
        (layout, logrecno, fileid, stusab, chariter, cifsn, t, geo_file) = map(row.pop, 
                ['layout', 'LOGRECNO', 'FILEID', 'STUSAB', 'CHARITER', 'CIFSN', 'type', 'geo_file'])
        (geo_file, geo_args) = geo_file
        logrecno = int(logrecno)
        geo = None
        if geo_file not in geoTables:
            geoTables = dict()
            geoTables[geo_file] = dict([ (lrn, dict([(k,d[k]) for k in filter(lambda x: x in required_geo_keys, d.keys())])) for lrn,d in census.build_geo_table(geo_file, geo_args).items() ])
        geo = geoTables[geo_file]
        if logrecno not in geo: continue
        if geo[logrecno]['SUMLEV'] in desired_sumlevs and 'P002001' in row:
            if geo[logrecno]['SUMLEV'] == 'DISTS' and \
                    not geo[logrecno]['CD110']: 
                        continue
            #print "inserting", geo[logrecno]['SUMLEV']
            db.insert('census_population', 
                    state_id = geo[logrecno]['STATE'],
                    county_id = geo[logrecno]['COUNTY'],
                    blockgrp_id = geo[logrecno]['BLKGRP'],
                    block_id = geo[logrecno]['BLOCK'],
                    district_id = geo[logrecno]['CD110'],
                    zip_id = geo[logrecno]['ZCTA5'],
                    sumlev = geo[logrecno]['SUMLEV'],
                    tract_id = geo[logrecno]['TRACT'],
                    area_land = geo[logrecno]['AREALAND'],
                    population = row['P002001'])
        #else: print "oops", geo[logrecno]['SUMLEV']
    print >>sys.stderr, "...Done loading census_population table."


def load_census_data(type):
    print >>sys.stderr, "Loading census_data table..."
    geoTables = {}
    for row in census.parse_sum_files([type]): #,requesting_keys[type]):
        (layout, logrecno, fileid, stusab, chariter, cifsn, t, geo_file) = map(row.pop, \
                ['layout', 'LOGRECNO', 'FILEID', 'STUSAB', 'CHARITER', 'CIFSN', 'type', 'geo_file'])
        (geo_file, geo_args) = geo_file
        logrecno = int(logrecno)
        if geo_file not in geoTables:
            reqed_keys = set(['LOGRECNO','SUMLEV','STATE','CD110'])
            tmp = census.build_geo_table(geo_file, geo_args)
            geoTables[geo_file] = dict([ (lrn, dict([(k,d[k]) for k in filter(lambda x: x in reqed_keys, d.keys())])) for lrn,d in tmp.items()])
        geo = geoTables[geo_file]
        if logrecno in geo:
            ### Entries for states
            loc_code = ''
            if geo[logrecno]['SUMLEV'] == 'STATE':
                loc_code = geo[logrecno]['STATE']
            ### Entries for the 110th Congress.
            elif geo[logrecno]['SUMLEV'] == 'DISTS' \
                    and geo[logrecno]['CD110']:
                loc_code = '%s-%02d' % (geo[logrecno]['STATE'], int(geo[logrecno]['CD110']))
            else: continue

            # Fix some districts:
            if loc_code in ['DC','PR']: loc_code = loc_code+'-00'
            if loc_code in ['DC-98','PR-98']: continue
            for internal_key, value in row.items():
                db.insert('census_data', seqname=False, district_id=loc_code, internal_key=internal_key, census_type=type, value=value)
    print >>sys.stderr, "...Done loading census_data table."

def main():
    for type in [1, 3]:
        load_census_meta(type)
        load_census_data(type)
    load_census_population()

if __name__ == "__main__":
    if batch_mode:
        from bulk_loader import bulk_loader_db
        db = bulk_loader_db(os.environ.get('WATCHDOG_TABLE', 'watchdog_dev'))
        meta_cols = ['internal_key', 'census_type', 'hr_key', 'label']
        db.open_table('census_meta', meta_cols, filename=tsv_file_format%'census_meta')
        data_cols = ['district_id', 'internal_key', 'census_type', 'value']
        db.open_table('census_data', data_cols, filename=tsv_file_format%'census_data')
        pop_cols = ['state_id', 'county_id', 'zip_id', 'tract_id', 'blockgrp_id', 'block_id', 'district_id', 'sumlev', 'population', 'area_land']
        db.open_table('census_population', pop_cols, filename=tsv_file_format%'census_population')
        main()
    else:
        from tools import db
        with db.transaction():
            #db.delete('census_data', where='1=1')
            #db.delete('census_meta', where='1=1')
            #db.delete('census_population', where='1=1')
            main()

