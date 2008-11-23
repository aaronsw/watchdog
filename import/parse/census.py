

## This assumes that the following files have been downloaded from the census
## bureau:
##     all_0Final_National.zip
##     all_0_National-part1.zip
##     all_0_National-part2.zip
##     sl500-in-sl010-us_h10.zip
##     sl500-in-sl010-us_s10.zip
##
## See: ../crawl/census.sh


import codecs
import csv
import fnmatch
import glob
import os
import re
import string
import sys
import time
import zipfile
from pprint import pprint, pformat

import fixed_width

DATA_DIR='../data/crawl/census/census_data'
#DATA_DIR='../../data/crawl/census/census_data/'
SAS_FORMAT='[sS][fF]%(type)d%(table)02d.[sS][aA][sS]'
ST_FORMAT='%(state)s000%(table)02d.uf%(type)d'
ST_GEO_FORMAT='%(state)sgeo.uf%(type)d'
UF_FORMAT='us000%(table)02d.uf%(type)d'
US_GEO_FORMAT='usgeo.uf%(type)d'
CONGRESS_DAT_FORMAT='sl500-in-sl040-%(state)s000%(table)02d.%(type_c)s10'
CONGRESS_GEO_FORMAT='sl500-in-sl040-%(state)sgeo.%(type_c)s10'
ST_CONGRESS_DAT_FORMAT='%(state)s000%(table)02d_%(type_c)s10'
ST_CONGRESS_GEO_FORMAT='%(state)sgeo_%(type_c)s10'
REDISTRICT_DAT_FORMAT='%(state)s000%(table)02d.upl'
REDISTRICT_GEO_FORMAT='%(state)sgeo.upl'
ALL_TABLES = { 1: range(1,40), 3: range(1,77) }
_text_encoding = 'latin-1' #'utf-8'

CENSUSSTATES = { 
        '01':'AL', '02':'AK', '04':'AZ', '05':'AR', '06':'CA', '08':'CO',
        '09':'CT', '10':'DE', '11':'DC', '12':'FL', '13':'GA', '15':'HI',
        '16':'ID', '17':'IL', '18':'IN', '19':'IA', '20':'KS', '21':'KY',
        '22':'LA', '23':'ME', '24':'MD', '25':'MA', '26':'MI', '27':'MN',
        '28':'MS', '29':'MO', '30':'MT', '31':'NE', '32':'NV', '33':'NH',
        '34':'NJ', '35':'NM', '36':'NY', '37':'NC', '38':'ND', '39':'OH',
        '40':'OK', '41':'OR', '42':'PA', '44':'RI', '45':'SC', '46':'SD',
        '47':'TN', '48':'TX', '49':'UT', '50':'VT', '51':'VA', '53':'WA',
        '54':'WV', '55':'WI', '56':'WY', '60':'AS', '66':'GU', '69':'MP',
        '72':'PR', '78':'VI', }

state_list = sorted(map(string.lower,CENSUSSTATES.values()))

SUMLEVs = { 
    '010':'US',
    '040':'STATE',
    '050':'COUNTY',
    '060':'COUNTYSUB',
    '070':'COUNTYSUBPLACE',
    '140':'TRACT',      # TRACT for countys
    '500':'DISTS',
    '511': 'TRACT',     # TRACT for districts
    '860':'ZCTA',       # National sf1 files
    '871':'ZCTA',       # State sf1 files
#    '080':'BLOCK',      # BLOCK for sf3
    '101':'BLOCK',      # BLOCK for sf1
#    '090':'BLKGRP',     # BLKGRP for sf3
    '091':'BLKGRP',     # BLKGRP for sf1
    '750':'BLOCK',      # BLOCK for Redistricting files
}

##TODO: some of these should be procesed as types other than strings.
GeoFields = {
        'D':[
            ('FILEID',    6,   fixed_width.string),
            ('STUSAB',    2,   fixed_width.string),
            ('SUMLEV',    3,   fixed_width.table_lookup(SUMLEVs)),
            #('SUMLEV',    3,   fixed_width.enum(**SUMLEVs)),
            ('GEOCOMP',   2,   fixed_width.string),
            ('CHARITER',  3,   fixed_width.string),
            ('CIFSN',     2,   fixed_width.string),
            ('LOGRECNO',  7,   fixed_width.integer),
            ('REGION',    1,   fixed_width.string),
            ('DIVISION',  1,   fixed_width.string),
            ('STATECE',   2,   fixed_width.string),
            ('STATE',     2,   fixed_width.table_lookup(CENSUSSTATES,  string.strip)),
            #('STATE',     2,   fixed_width.enum(**CENSUSSTATES)),
            ('COUNTY',    3,   fixed_width.string),
            ('COUNTYSC',  2,   fixed_width.string),
            ('COUSUB',    5,   fixed_width.string),
            ('COUSUBCC',  2,   fixed_width.string),
            ('COUSUBSC',  2,   fixed_width.string),
            ('PLACE',     5,   fixed_width.string),
            ('PLACECC',   2,   fixed_width.string),
            ('PLACEDC',   1,   fixed_width.string),
            ('PLACESC',   2,   fixed_width.string),
            ('TRACT',     6,   fixed_width.string),
            ('BLKGRP',    1,   fixed_width.string),
            ('BLOCK',     4,   fixed_width.string),
            ('IUC',       2,   fixed_width.string),
            ('CONCIT',    5,   fixed_width.string),
            ('CONCITCC',  2,   fixed_width.string),
            ('CONCITSC',  2,   fixed_width.string),
            ('AIANHH',    4,   fixed_width.string),
            ('AIANHHFP',  5,   fixed_width.string),
            ('AIANHHCC',  2,   fixed_width.string),
            ('AIHHTLI',   1,   fixed_width.string),
            ('AITSCE',    3,   fixed_width.string),
            ('AITS',      5,   fixed_width.string),
            ('AITSCC',    2,   fixed_width.string),
            ('ANRC',      5,   fixed_width.string),
            ('ANRCCC',    2,   fixed_width.string),
            ('MSACMSA',   4,   fixed_width.string),
            ('MASC',      2,   fixed_width.string),
            ('CMSA',      2,   fixed_width.string),
            ('MACCI',     1,   fixed_width.string),
            ('PMSA',      4,   fixed_width.string),
            ('NECMA',     4,   fixed_width.string),
            ('NECMACCI',  1,   fixed_width.string),
            ('NECMASC',   2,   fixed_width.string),
            ('EXI',       1,   fixed_width.string),
            ('UA',        5,   fixed_width.string),
            ('UASC',      2,   fixed_width.string),
            ('UATYPE',    1,   fixed_width.string),
            ('UR',        1,   fixed_width.string),
            ('CD106',     2,   fixed_width.string),
            ('CD108',     2,   fixed_width.string),
            ('CD109',     2,   fixed_width.string),
            ('CD110',     2,   fixed_width.string),
            ('SLDU',      3,   fixed_width.string),
            ('SLDL',      3,   fixed_width.string),
            ('VTD',       6,   fixed_width.string),
            ('VTDI',      1,   fixed_width.string),
            ('ZCTA3',     3,   fixed_width.string),
            ('ZCTA5',     5,   fixed_width.string),
            ('SUBMCD',    5,   fixed_width.string),
            ('SUBMCDCC',  2,   fixed_width.string),
            ('AREALAND',  14,  fixed_width.integer),
            ('AREAWATR',  14,  fixed_width.integer),
            ('NAME',      90,  fixed_width.string),
            ('FUNCSTAT',  1,   fixed_width.string),
            ('GCUNI',     1,   fixed_width.string),
            ('POP100',    9,   fixed_width.integer),
            ('HU100',     9,   fixed_width.integer),
            ('INTPLAT',   9,   fixed_width.integer),
            ('INTPLON',   10,  fixed_width.integer),
            ('LSADC',     2,   fixed_width.string),
            ('PARTFLAG',  1,   fixed_width.string),
            ('SDELEM',    5,   fixed_width.string),
            ('SDSEC',     5,   fixed_width.string),
            ('SDUNI',     5,   fixed_width.string),
            ('TAZ',       6,   fixed_width.string),
            ('UGA',       5,   fixed_width.string),
            ('PUMA5',     5,   fixed_width.string),
            ('PUMA1',     5,   fixed_width.string),
            ('RESERVE2',  15,  fixed_width.string),
            ('MACC',      5,   fixed_width.string),
            ('UACP',      5,   fixed_width.string),
            ('RESERVED',  7,   fixed_width.string),
        ]}


def parse_geo_file(fn, args):
    GF= {'D': list(GeoFields['D'])}
    if 'usgeo' in fn or 'by_state' in fn:
        # The geo files for usgeo.* use dos line breaks...
        GF['D'].append((None, 2, fixed_width.filler))
    else:
        # ... the congress geo files use unix line breaks.
        GF['D'].append((None, 1, fixed_width.filler))
    GF['D'].append(('geo_file', 0, lambda x: fn))
    print fn
    #file = codecs.open(fn, 'r', encoding=_text_encoding)
    file = getFile(os.path.dirname(fn), os.path.basename(fn), args)
    return fixed_width.parse_file(GF, file,lambda x:'D')


def makePath(l):
    p = ""
    for i,x in enumerate(l):
        x = x.strip()
        x[0].lower()
        x = x.replace('-','')
        x = x.split()[0] + ''.join(string.capwords(x).split()[1::])
        x = ''.join(filter(lambda c: c not in string.punctuation,list(x)))
        if i != len(l)-1 and x == "Total":
            continue
        p = "%s/%s" % (p,x)
    return p

def getIndent(s):
    return len(s) - len(s.lstrip())

def getFile(dir, fn_format, args1=None):
    path_to_zipfiles = {
            DATA_DIR + '/table_layouts': ["SF%(type)sSAS.zip", ],
            DATA_DIR + '/by_state': ["%(state)s000%(table)02d_uf%(type)d.zip", "%(state)sgeo_uf%(type)d.zip"],
            DATA_DIR + '/congress': ["%(state)s000%(table)02d_%(type_c)s10.zip", "%(state)sgeo_%(type_c)s10.zip", "sl500-in-sl040-%(state)s_%(type_c)s10.zip"],
            DATA_DIR: ["us%(table)05d_uf%(type)d.zip", "usgeo_uf%(type)d.zip"], 
            }
    args = dict(type=None, type_c=None, table=None, state=None)
    if args1: args.update(args1)
    type_c = { 1: 'h', 3:'s'}
    if not args['type_c'] and args['type']: args['type_c']=type_c[args['type']]
    #print pformat(args), dir, fn_format
    fn = glob.glob((dir+'/'+fn_format) % args)
    #if False and fn: # For now force from zipfile.
    if fn:
        if len(fn) != 1: return None # Woah, matched multiple files
        print fn[0]
        return codecs.open(fn[0], 'r', encoding=_text_encoding)
    else: # Try zip files
        r = re.compile(fnmatch.translate(fn_format%args))
        for zipfn in path_to_zipfiles[dir]:
            if not glob.glob(dir+'/'+zipfn%args): continue
            zf = zipfile.ZipFile(dir+'/'+zipfn%args)
            files = zf.namelist()
            for f in files: 
                if r.match(f):
                    print "%s/%s -> %s" % (dir, zipfn%args, f)
                    return codecs.EncodedFile(zf.open(f), _text_encoding) ## Requires zipfile from python 2.6
                    #return zf.read(f).splitlines(True)
    print "Couldn't find file %s in %s." % \
            ((dir+'/'+fn_format) % args, pformat(map(lambda x: (x % args), path_to_zipfiles[dir])))
    return []


def parse_sas_file(type, table, pathMap={}):
    #TODO: - Should be able to handle LENGTH section 
    #        and '... $ start-end' input lines.
    labelRE = re.compile(r'^\s*.*?\s*(\S+)=\'(.*)\'\s*.*$')
    inputRE = re.compile(r'^\s*([^\s;]+)\s*.*$')
    universeRE = re.compile(r'\/\*Universe: (.+)*\*\/')
    labelMap = {}    # Mapping from the census keys to the lables
    fieldList = []   # ordered list of fields
    path=[]          # 
    state = 'INIT'
    
    for line in getFile(DATA_DIR+'/table_layouts',SAS_FORMAT, {'type':type,'table':table}):
        if state == 'INIT':
            if 'LABEL' in line:
                state = 'LABEL'
        if state == 'LABEL':
            if 'INPUT' in line:
                state = 'INPUT'
                continue
            for u in universeRE.findall(line):
                path = [u]
            for l in labelRE.findall(line):
                labelMap[l[0]] = l[1]
                if path:
                    l_indent = getIndent(l[1])
                    while len(path)>1: # don't pop universe
                        curIndent=getIndent(path[-1])
                        if l_indent > curIndent: break
                        path.pop()
                    path.append(l[1])
                    path_str = makePath(path) 
                    if path_str not in pathMap:
                        pathMap[path_str] = set([ l[0] ])
                    else:  
                        pathMap[path_str].add( l[0] )
        if state == 'INPUT':
            if 'RUN' in line:
                break
            for i in inputRE.findall(line):
                fieldList.append(i)
    return (fieldList,labelMap,pathMap)


def parse_state_sum_file(type, table, state, layout):
    FIELDs = layout[0]
    args = { 'state':state, 'type':type, 'table':table }
    dat_fn = (DATA_DIR + '/by_state/' + ST_FORMAT) % args
    geo_fn = (DATA_DIR + '/by_state/' + ST_GEO_FORMAT) % args
    return _parse_sum_file(dat_fn, geo_fn, FIELDs, args)

def parse_congress_file(type, table, state, layout, use_st=True):
    FIELDs = layout[0]
    type_c = { 1: 'h', 3:'s'}
    args = {'type_c':type_c[type], 'state':state, 'table':table, 'type':type}
    if use_st:
        dat_fn = DATA_DIR + '/congress/' + ST_CONGRESS_DAT_FORMAT % args
        geo_fn = DATA_DIR + '/congress/' + ST_CONGRESS_GEO_FORMAT % args
    else:
        dat_fn = DATA_DIR + '/congress/' + CONGRESS_DAT_FORMAT % args
        geo_fn = DATA_DIR + '/congress/' + CONGRESS_GEO_FORMAT % args
    return _parse_sum_file(dat_fn, geo_fn, FIELDs, args)

def parse_redistrict_file(type, table, state, layout):
    FIELDs = layout[0]
    args = {'state':state, 'table':table, 'type':type}
    dat_fn = DATA_DIR + '/Redistrict/' + REDISTRICT_DAT_FORMAT % args
    geo_fn = DATA_DIR + '/Redistrict/' + REDISTRICT_GEO_FORMAT % args
    return _parse_sum_file(dat_fn, geo_fn, FIELDs, args)

def parse_sum_file(type, table, layout):
    FIELDs = layout[0]
    args = { 'type':type, 'table':table }
    dat_fn = (DATA_DIR + '/' + UF_FORMAT) % args
    geo_fn = (DATA_DIR + '/' + US_GEO_FORMAT) % args
    return _parse_sum_file(dat_fn, geo_fn, FIELDs, args)


def _parse_sum_file(dat_fn, geo_fn, FIELDs, args):
    file = getFile(os.path.dirname(dat_fn),os.path.basename(dat_fn), args)
    if not file: return
    c = csv.reader(file)
    for row in c:
        d = dict(zip(FIELDs,row))
        if geo_fn: d['geo_file'] = (geo_fn, args)
        yield d


### ARRG, we *MUST* be able to get blocks within districts, they even give us a
#   file that tells us when there is overlap:
#   http://www.census.gov/geo/www/cd110th/spblk110.txt
def parse_state_sum_files(types=[1,3], ReqKeyList=None):
    # About 19403085 records!
    type = 1
    table = 1
    all_keys = {}
    layout = parse_sas_file(type, table,all_keys)
    for state in state_list:
        ## Check if this file has any of the keys we want.
        if ReqKeyList :
            want = set(ReqKeyList)
            have = set(layout[0])
            if not have.intersection(want): continue
        #pprint(layout[1])
        for parser_fn in [parse_congress_file, parse_state_sum_file]:
            numRows = 0
            start_time = time.time()
            for row in parser_fn(type, table, state, layout):
                row['type']=type
                row['layout']=layout
                numRows += 1
                yield row
            print "Summary file processed with %d rows in %.4f seconds." % \
                    (numRows, time.time()-start_time)

def parse_sum_files(types=[1,3], ReqKeyList=None):
    # About 19403085 records!
    tables = ALL_TABLES
    for type in types:
        all_keys = {}
        for table in tables[type]:
            layout = parse_sas_file(type, table, all_keys)
            ## Check if this file has any of the keys we want.
            if ReqKeyList :
                want = set(ReqKeyList)
                have = set(layout[0])
                if not have.intersection(want): continue
            #pprint(layout[1])
            numRows = 0
            start_time = time.time()
            for row in parse_sum_file( type, table, layout ):
                row['type']=type
                row['layout']=layout
                numRows += 1
                yield row
            print "Summary file processed with %d rows in %.4f seconds." % \
                    (numRows, time.time()-start_time)
            numRows = 0
            start_time = time.time()
            for state in state_list:
                for row in parse_congress_file(type, table, state, layout, use_st=False):
                    row['type']=type
                    row['layout']=layout
                    numRows += 1
                    yield row
            print "Congress summary file(s) processed with %d rows in %.4f seconds." % \
                    (numRows, time.time()-start_time)

################################################################################
def print_sum_files():
    geoTables = {}
    for row in parse_sum_files():
        (geo_file, geo_args) = row['geo_file']
        if geo_file in geoTables:
            geo = geoTables[geo_file]
        else:
            geoTables[geo_file] = build_geo_table(geo_file, geo_args)
            geo = geoTables[geo_file]
        layout = row['layout']
        if row['LOGRECNO'] in geo:
            print "Found geo data for:", row['LOGRECNO'], "as", geo[row['LOGRECNO']]
        else: 
            print "Didn't find geo data for:",row['LOGRECNO']
        kk = row.keys()
        kk.remove('layout')
        kk.remove('type')
        kk.sort()
        for k in kk:
            if k in layout[1]:
                print '%-45s .......... %s'%(layout[1][k][0:45],row[k])
            else:
                print '%-45s .......... %s'%(k,row[k])
        print '='*80


def build_geo_table(fn, args):
    LOGRECNOs = {}
    numRows=0
    start_time = time.time()
    for row in parse_geo_file(fn, args):
        numRows += 1
        if row['GEOCOMP'] != '00':  ## We only care about geo code 00 for now.
            continue
        LOGRECNOs[row['LOGRECNO']] = row
    print "Geo table processed with %d rows in %.4f seconds." % \
            (numRows, time.time()-start_time)
    return LOGRECNOs


def process_all_sas():
    tables = { 1: range(1,40), 3: range(1,77) }
    for type in [1,3]:
        all_keys = {}
        for table in tables[type]:
            layout = parse_sas_file(type,table,all_keys)
        pprint(all_keys)

################################################################################
if __name__ == "__main__":
    #process_all_sas()
    print_sum_files()
    ## Just to do the following iteration through the data takes about an hour.
    #for row in parse_sum_files():
    #    pass
