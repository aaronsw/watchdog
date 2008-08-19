# historical_voting.py - Parse and import historical voting by county
# fors years 1964 - 2004
# Copyright (C) 2008 didier deshommes <dfdeshom@gmail.com>

STATE_CODES = '../data/crawl/manual/rvdb/state_codes'
DATA_PATH = '../data/crawl/manual/rvdb/allYears/'

import glob

def read_state_codes(fname):
    """
    Read in state codes file and store in a dict
    """
    fdata = file(fname).readlines()
    state_codes = {}
    for line in fdata:
        line = line.split(' ',1)
        state_codes[line[0]] = line[1].strip().lower().replace(' ','_')

    return state_codes
    
def parse_historical_voting():
    """
    parse County-level data. The data is in this format
    STATE_CODE  COUNTY_NAME DEMOCRAT_COUNT REPUBLICAN_COUNT OTHER_COUNT
    """
    
    election_results = {}
    election_data = {}
    state_codes = read_state_codes(STATE_CODES)
    files = glob.glob(DATA_PATH+'*')
    
    for fname in files[:-1]: # skip junk file
        for line in file(fname).readlines():
            code, county_name, numbers = line.split('"')
            dem_count, rep_count, other_count = numbers.split()
            state = state_codes[code.strip()]
        
            yield {'dem_count':dem_count,
                   'rep_count':rep_count,
                   'other_count':other_count,
                   'state': state,
                   'county_name': county_name,
                   'year':fname.split('/')[-1]}
           
    
if __name__ == "__main__":
    import tools
    tools.export(parse_historical_voting())
