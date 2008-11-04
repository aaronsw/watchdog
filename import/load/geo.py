import sys

from settings import db
from decimal import *

################################################################################
def county2dist(state, county, scale_column='population'):
    # The census provides both county and districts at the tract level
    pop_county = db.select('census_population', what='sum('+scale_column+')',
            where="sumlev='COUNTY' and state_id=$state and county_id=$county",
            vars=locals()).list()
    if pop_county and len(pop_county)==1:
        pop_county = pop_county[0].sum
    else: print "oops"; return None
    intersect_pops = db.select('census_population', 
            what='district_id, sum('+scale_column+')', 
            where="sumlev='TRACT' and district_id != '' and state_id=$state and county_id=$county", 
            group='district_id', vars=locals())

    ret = {}
    for ip in intersect_pops:
        ret['%s-%s' % (state, ip.district_id)] = Decimal(ip.sum) / pop_county if pop_county else 0.0
    return ret


def zip2dist_by_zip4(zip5):
    if db.select('state', where='code=$zip5',vars=locals()):
        return {zip5:1.0}
    dists  = db.select('zip4', 
            what='COUNT(plus4), district_id', 
            where='zip=$zip5', 
            group='district_id',
            vars=locals()).list()
    all_zip4 = sum(map(lambda d: d.count, dists))
    ret = {}
    for d in dists:
        ret[d.district_id] = float(d.count) / float(all_zip4)
    return ret

def zip2dist(zip5, scale_column='population'):
    ## ARRRG, The census provides the congressional districts down to the tract
    # level, but not to the block level. The ZCTA are provided at the block
    # level, but NOT at the tract level. 
    # This would be ok if tracts didn't overlap ZCTAs, but they do. Not sure
    # how to solve this problem.
    if scale_column=='zip4':
        return zip2dist_by_zip4(zip5)
    pop_zip = db.select('census_population', what='sum('+scale_column+')',
            where="sumlev='ZCTA' and zip_id=$zip5",
            vars=locals()).list()
    if pop_zip and len(pop_zip)==1:
        pop_zip = pop_zip[0].sum
    else: print "oops"; return None
    # Limit our search to known intersecting districts
    dists = db.select('zip4', what='district_id', 
            where="zip=$zip5", group='district_id', 
            vars=locals())

    intersect_pops = db.query("select a.district_id, b.state_id, SUM(b."+scale_column+") from (SELECT * FROM census_population WHERE sumlev='TRACT' AND district_id != '') as a INNER JOIN (SELECT * FROM census_population WHERE sumlev='BLOCK' AND zip_id=$zip5) as b ON (a.state_id=b.state_id AND a.county_id=b.county_id AND a.tract_id=b.tract_id) group by a.district_id, b.state_id", vars=locals()).list()

    # NOTE: This is not the correct behavior, but for now just adjust this to
    #       give us something that sums to 1.0.
    pop_zip2 = sum(map(lambda x: x.sum if x.sum else 0.0, intersect_pops))
    print >>sys.stderr, "Pop Zip:",pop_zip, pop_zip2
    pop_zip = pop_zip2

    ret = {}
    for ip in intersect_pops:
        print >>sys.stderr, ip.sum, pop_zip
        ret['%s-%s' % (ip.state_id, ip.district_id)] = Decimal(ip.sum) / pop_zip if pop_zip else 0.0
    return ret


counties = [('CA','067'),]
for state,county in counties:
    c = county2dist(state,county)
    print "County(%s-%s) to district by population"%(state,county), c, sum(c.values())
    c = county2dist(state, county, scale_column='area_land')
    print "County(%s-%s) to district by area"%(state,county), c, sum(c.values())

zips = ['95835', '95608', '10024', ]
for zip in zips:
    z = zip2dist(zip)
    print "Zip(%s) to district by population" % zip, z, sum(z.values())
    z = zip2dist(zip, scale_column='area_land')
    print "Zip(%s) to district by area" % zip, z, sum(z.values())
    z = zip2dist(zip, scale_column='zip4')
    print "Zip(%s) to district by zip4s" % zip, z, sum(z.values())


