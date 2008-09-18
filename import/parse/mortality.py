"""
Imports NCHS (National Center for Health Statistics) 
mortality data scraped from http://wonder.cdc.gov
"""

__author__ = 'garryj'

import csv
import web
import pprint
import re

def parse_line(x):
    out = web.storage()
    out.county_name = x['County']
    out.county_fips = x['County Code']
    out.cause_name = x['Cause of death']
    out.cause_code = x['Cause of death Code']
    if re.search(r'Suppressed', x['Count']):
        out.deaths_suppressed = True
    else:
        out.deaths_suppressed = False
        out.deaths = x['Count']
    out.population = x['Population']
    if re.search(r'Suppressed', x['Crude Rate']):
        out.crude_rate_suppressed = True
    else:
        out.crude_rate_suppressed = False
        crude_rate = re.search(r'(?P<rate>\d*(\.\d*))', x['Crude Rate'])
        if crude_rate:
            out.crude_rate = crude_rate.group('rate')
        unreliable = re.search(r'Unreliable', x['Crude Rate'])
        out.crude_rate_reliable = False if unreliable else True
    return out

def parse_file(fn):
    parser = csv.DictReader(file(fn), delimiter="\t")
    for x in parser:
        # IgnoreTotal and footer lines
        if x['Notes']=="Total" or x['Count']==None:
            continue
        else:
            yield parse_line(x)

if __name__=="__main__":
    import tools
    import sys
    for i in sys.argv[1:]:
        tools.export(parse_file(i))
