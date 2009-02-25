"""
import voteview
"""

import tools
from parse import voteview
from settings import db

def main():
    for pol in voteview.parse():
        if not pol.get('district_id'): continue #@@
    
        if not tools.districtp(pol.district_id) and pol.district_id.endswith('01'):
            pol.district_id = pol.district_id.split('-')[0] + '-' + '00'
    
        watchdog_id = tools.getWatchdogID(pol.district_id, pol.last_name)
        if watchdog_id:
            db.update('politician', where='id=$watchdog_id', vars=locals(),
              icpsrid = pol.icpsr_id, 
              nominate = pol.dim1, 
              predictability = 1 - (pol.n_errs / float(pol.n_votes)))

if __name__ == "__main__": main()
