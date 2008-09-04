from __future__ import with_statement
from pprint import pprint, pformat
import sys
from types import NoneType

import web

from parse import soi
from tools import db


# The keys from the parser are:
# {
#     'loc', 'gini', 
#     'brackets' : 
#     {
#         'agi', 'bracket_low', 
#         'n_dependents', 'n_eitc', 'n_filers', 'n_prepared', 
#         'tot_charity', 'tot_eitc', 'tot_tax', 
#         'avg_dependents', 'avg_eitc', 'avg_income', 'avg_taxburden', 
#         'pct_charity', 'pct_eitc', 'pct_prepared', 
#     }
# }

# NOTE: I am using the number of zip+4's in a zip/district to determine the
#       proportion of that zip's data to apply to a district.
def get_dist(zip5):
    # TODO: if zip5 is state (select code from state where code=$zip5) then return {zip5: 1.0}
    if db.select('state', where='code=$zip5',vars=locals()):
        return {zip5:1.0}
    dists  = db.select('zip4', 
            what='COUNT(plus4), district', 
            where='zip=$zip5', 
            group='district',
            vars=locals()).list()
    all_zip4 = sum(map(lambda d: d.count, dists))
    ret = {}
    for d in dists:
        ret[d.district] = float(d.count) / float(all_zip4)
    return ret


def load_soi():
    # TODO: not sure how to handle agi and gini values.
    districts = {}
    data = {}
    for z in soi.parse_soi():
        dists_for_data = get_dist(z.loc)
        if dists_for_data:
            data[z.loc] = z
            for d in dists_for_data.keys():   # for each district associated with loc
                if d not in districts:
                    districts[d] = { 'brackets': [{'n_filers':0} for x in range(len(z.brackets))] }
                for new_data,cur_data in zip(z.brackets, districts[d]['brackets']):
                    #print new_data.n_filers, new_data.n_prepared, new_data.agi, new_data.bracket_low
                    n_filers_old = cur_data['n_filers']
                    if not new_data.n_filers: new_data['n_filers'] = 0
                    n_filers_new = n_filers_old + new_data.n_filers * dists_for_data[d]
                    for k in new_data.keys():
                        if k not in cur_data:
                            cur_data[k] = 0
                        if k.startswith('n_') or k.startswith('tot_') or k == 'agi':
                            if new_data[k]:
                                cur_data[k] += new_data[k] * dists_for_data[d]
                        elif k.startswith('pct_') or k.startswith('avg_'):
                            if new_data[k]:
                                cur_data[k] = (cur_data[k] * n_filers_old + dists_for_data[d] * new_data[k] * new_data.n_filers) / n_filers_new
                        else:
                            #if k in cur_data and cur_data[k] != new_data[k]: print k, cur_data[k], new_data[k]
                            cur_data[k] = new_data[k]
    for d in districts.keys():
        for b in districts[d]['brackets']:
            if isinstance(b['bracket_low'], NoneType): b['bracket_low'] = -1
            db.insert('soi', seqname=False, location=d, **b)
    #pprint(districts)


if __name__ == "__main__":
    load_soi()


