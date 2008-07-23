"""
Parse IRS SOI statistics.
"""

import web
import xls2list

SOI_PATH = "../data/crawl/irs/soi/2005/ZIP Code 2005 %s.xls"

class MissingData(Exception): pass
def gini_est(data):
    """
    Estimates upper and lower bounds for Gini coefficient based on
    equations 1.1 thru 1.3 from Mehran 1975 as summarized in
    Gastwirth 1972 at <http://www.jstor.org/stable/2285377?seq=1>.
    
    `data` is a list of dictionaries with the keys
    `lower_bound`, `n_filers`, and `adjusted_gross_income`.
    The first dictionary should have `lower_bound = None`
    and contain the totals for the set.
    """
    def fraction(i, col):
        out = 0.
        for n, x in enumerate(data):
            if x[col] is None:
                raise MissingData, col
            if n == 0:
                total = x[col]
            else:
                out += x[col]
            if n == i: break
        return out/total

    people_f = lambda i: fraction(i, 'n_filers')
    income_f = lambda i: fraction(i, 'agi')

    def mean_r(i):
        if data[i].agi == 0: return 0
        return float(data[i].agi)/data[i].n_filers

    def topof(i):
        if i < len(data)-1:
            return data[i+1].bracket_low
        else:
            return data[-1].agi

    ksum = 0
    for i in range(1, len(data)):
    	ksum += (people_f(i) - people_f(i-1)) * \
    	        (income_f(i) + income_f(i-1))
    lower_bound = 1 - ksum

    dsum = 0
    for i in range(1, len(data)):
    	dsum += (people_f(i) - people_f(i-1))**2 * \
    	        (topof(i) - mean_r(i)) * \
    	        (mean_r(i) - topof(i-1)) * \
    	        (topof(i) - topof(i-1))**-1
    grouping = mean_r(0)**-1 * dsum
    upper_bound = lower_bound + grouping

    return lower_bound, upper_bound

def parse_state(state):
    def fixnum(x, multiply=1):
        if isinstance(x, unicode) and '*' in x:
            return None
        else:
            return x * multiply
    
    stats = xls2list.xls2list(SOI_PATH % state)
    
    loc = 11 # rest is all headers
    while loc+7 < len(stats):
        out = web.storage()
        bundle = stats[loc:loc+7]
        if bundle[0][0] == None:
            break

        out.loc = bundle[0][0]
        if isinstance(out.loc, float):
            out.loc = str(int(out.loc)).zfill(5)
        
        if out.loc.strip() == "MISSOURI":
            loc += 8 # duped data
            continue

        out.brackets = []
        
        for line in bundle:
            if (isinstance(line[0], unicode) and line[0].strip() == 'Total'
               ) or isinstance(line[0], float):
                line[0] = None
            elif line[0].strip() == "Under $10,000":
                line[0] = 0
            else:
                line[0] = int(''.join([x for x in line[0].split()[0] if x.isdigit()]))
            out.brackets.append(web.storage(
              bracket_low=line[0], 
              n_filers=fixnum(line[1]), 
              agi=fixnum(line[4], 1000),
              tot_tax=fixnum(line[35], 1000),
              n_dependents=fixnum(line[3]),
              n_eitc=fixnum(line[36]),
              tot_eitc=fixnum(line[37], 1000),
              tot_charity=fixnum(line[26], 1000),
              n_prepared=fixnum(line[38])
            ))
            
            br = out.brackets[-1]            
            err = (TypeError, ZeroDivisionError)
            
            try: br.pct_prepared = float(br.n_prepared)/br.n_filers
            except err: pass

            try: br.pct_charity = float(br.tot_charity)/br.agi
            except err: pass

            try:
                br.avg_eitc = float(br.tot_eitc)/br.n_eitc
            except TypeError:
                pass
            except ZeroDivisionError:
                br.avg_eitc = 0

            try: br.pct_eitc = float(br.n_eitc)/br.n_filers
            except err: pass

            try: br.avg_dependents = float(br.n_dependents)/br.n_filers
            except err: pass

            try: br.avg_taxburden = float(br.tot_tax)/br.agi
            except err: pass

            try: br.avg_income = float(br.agi)/br.n_filers
            except err: pass
                
        try: out.gini = gini_est(out.brackets)
        except MissingData: pass
        
        yield out
        
        loc += 8

def parse_soi():
    states = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 
    'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 
    'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 
    'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 
    'WA', 'WI', 'WV', 'WY']
    
    for state in states:
        import sys
        print>>sys.stderr, state
        for x in parse_state(state):
            if x.loc.strip() == 'Total':
                x.loc = state
            yield x

if __name__ == "__main__":
    import tools
    tools.export(parse_soi())
