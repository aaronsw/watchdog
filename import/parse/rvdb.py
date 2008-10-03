# historical_voting.py - Parse and import historical voting by county
# fors years 1964 - 2004
# Copyright (C) 2008 didier deshommes <dfdeshom@gmail.com>

STATE_CODES = '../data/crawl/manual/rvdb/state_codes'
DATA_PATH = '../data/crawl/manual/rvdb/allYears/'

import glob

def read_state_codes(fname=STATE_CODES):
    """Turn `fname` into a dict."""
    state_codes = {}
    for line in file(fname).readlines():
        line = line.split(' ',1)
        state_codes[line[0]] = line[1].strip().title()
    return state_codes

def parse_historical_voting():
    """
    Parse county-level data. The data is in the format:
    STATE_CODE  COUNTY_NAME DEMOCRAT_COUNT REPUBLICAN_COUNT OTHER_COUNT
    """
    state_codes = read_state_codes()
    files = glob.glob(DATA_PATH + '*')
    
    for fname in files[:-1]: # skip junk file
        for line in file(fname).readlines():
            code, county_name, numbers = line.split('"')
            dem_count, rep_count, other_count = numbers.split()
            state = state_codes[code.strip()]
        
            yield {
              'n_democrats': dem_count,
              'n_republicans': rep_count,
              'n_other': other_count,
              'state_name': state,
              'state_fips': code.strip(),
              'county_name': county_name,
              'year': fname.split('/')[-1]
            }

if __name__ == "__main__":
    import tools
    tools.export(parse_historical_voting())
