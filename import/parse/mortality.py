"""
Imports NCHS (National Center for Health Statistics) 
mortality data scraped from http://wonder.cdc.gov
"""

__author__ = 'garryj'

import re, csv
from glob import glob
import web

from fips import CENSUSSTATES

DATA_DIR='../data'


FILES=[DATA_DIR+'/crawl/mortality/%s.tsv' % x for x in CENSUSSTATES.values()]


def parse_line(x):
    out = web.storage()
    out.county_name = x['County']
    out.state=CENSUSSTATES[x['County Code'][:2]]
    out.county_fips = x['County Code'][2::]
    out.cause_name = x['Cause of death']
    out.cause_code = x['Cause of death Code']
    if 'Suppressed' in x['Count']:
        out.deaths_suppressed = True
    else:
        out.deaths_suppressed = False
        out.deaths = x['Count']
    out.population = x['Population']
    if 'Suppressed'  in x['Crude Rate']:
        out.crude_rate_suppressed = True
    else:
        out.crude_rate_suppressed = False
        crude_rate = re.search(r'(?P<rate>\d*(\.\d*))', x['Crude Rate'])
        if crude_rate:
            out.crude_rate = crude_rate.group('rate')
        unreliable = 'Unreliable' in x['Crude Rate']
        out.crude_rate_reliable = not unreliable
    return out

def parse_file(fn):
    if not glob(fn):
        return 
    parser = csv.DictReader(file(fn), delimiter="\t")
    for x in parser:
        # IgnoreTotal and footer lines
        if x['Notes'] == "Total" or x['Count'] == None:
            continue
        else:
            yield parse_line(x)

if __name__=="__main__":
    import sys
    import tools
    for i in sys.argv[1:]:
        tools.export(parse_file(i))
