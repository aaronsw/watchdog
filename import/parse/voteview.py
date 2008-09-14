"""
parse voteview partisanship data
"""

HOUSE_DAT = "../data/crawl/voteview/HL01110C21_PRES_BSSE.DAT"
SENATE_DAT = "../data/crawl/voteview/SL01110C21_BSSE.dat"

state_map = { #@@ import to state json as icpsr
  41: 'AL', 81: 'AK', 61: 'AZ', 42: 'AR', 71: 'CA', 62: 'CO', 1: 'CT',
  11: 'DE', 43: 'FL', 44: 'GA', 82: 'HI', 63: 'ID', 21: 'IL', 22: 'IN',
  31: 'IA', 32: 'KS', 51: 'KY', 45: 'LA', 2: 'ME', 52: 'MD', 3: 'MA',
  23: 'MI', 33: 'MN', 46: 'MS', 34: 'MO', 64: 'MT', 35: 'NE', 65: 'NV',
   4: 'NH', 12: 'NJ', 66: 'NM', 13: 'NY', 47: 'NC', 36: 'ND', 24: 'OH',
  53: 'OK', 72: 'OR', 14: 'PA',  5: 'RI', 48: 'SC', 37: 'SD', 54: 'TN',
  49: 'TX', 67: 'UT', 6: 'VT', 40: 'VA', 73: 'WA', 56: 'WV', 25: 'WI',
  68: 'WY', 55: 'DC'
}

import web
import tools

def parse():
   for fn in [HOUSE_DAT, SENATE_DAT]:
       for line in file(fn):
           out = web.storage()
           out.congress = int(line[0:4])
           out.icpsr_id = int(line[4:10])
           out.icpsr_state = int(line[10:13])
           out.district = int(line[13:15])        
           out.state_name = line[15:23].strip()
           out.party_code = int(line[23:28])
           out.last_name = line[28:41].strip()
           out.dim1 = float(line[41:47])
           out.dim2 = float(line[47:54])
           out.std1 = float(line[54:61])
           out.std2 = float(line[61:68])
           out.corr = float(line[68:75])
           out.loglike = float(line[75:87])
           out.n_votes = int(line[87:92])
           out.n_errs = int(line[92:97])
           out.n_geomeanprob = float(line[97:104])
           
           if out.icpsr_state in state_map:
               out.state_code = state_map[out.icpsr_state]
               if out.district:
                   out.district_id = out.state_code + '-' + str(out.district).zfill(2)
               else:
                   out.district_id = out.state_code 
           
           yield out

if __name__ == "__main__":
    tools.export(parse())
