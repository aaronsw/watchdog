"""
import voteview
"""

import simplejson
from parse import voteview
import tools

out = {}
for pol in voteview.parse():
    if pol.congress != 110 or not pol.get('district_id'): continue #@@
    
    if not tools.districtp(pol.district_id) and pol.district_id.endswith('01'):
        pol.district_id = pol.district_id.split('-')[0] + '-' + '00'

    watchdog_id = tools.districtp(pol.district_id)
    if watchdog_id:
        out[watchdog_id] = {
          'icpsrid': pol.icpsr_id,
          'nominate': pol.dim1,
          'predictability': 1 - (pol.n_errs / float(pol.n_votes))
        }

if __name__ == "__main__":
    print simplejson.dumps(out, indent=2, sort_keys=True)
