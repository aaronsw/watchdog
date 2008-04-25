import os, glob
import simplejson
import web
import cgitb
cgitb.enable(format='text')

DATA_DIR = '../data/load'
db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'), db='watchdog_dev')

def unidecode(d):
    newd = {}
    for k, v in d.iteritems():
        newd[k.encode('utf8')] = v
    return newd

def items(fname):
    print 'loading', fname
    return simplejson.load(file(DATA_DIR + '/%s.json' % fname)).iteritems()

def load_all():
    for code, state in items('states/index'):
        if 'aka' in state: state.pop('aka')
        db.insert('state', seqname=False, code=code, **unidecode(state))
    
    for name, district in items('districts/index'):
        db.insert('district', seqname=False, name=name, **unidecode(district))
    
    for fn in ['almanac', 'shapes', 'centers']:
        for name, district in items('districts/' + fn):
            if 'interest_group_rating' in district:
                district.pop('interest_group_rating')
            db.update('district',
                      where='name = $name',
                      vars=locals(),
                      **unidecode(district))

    district_to_pol = {}
    for polid, pol in items('politicians/index'):
        db.insert('politician', seqname=False, id=polid, **unidecode(pol))
        district_to_pol[pol['district']] = polid
    
    for fn in ['govtrack', 'photos']:
        for polid, pol in items('politicians/' + fn):
            db.update('politician',
                      where='id = $polid',
                      vars=locals(),
                      **unidecode(pol))

    for name, district in items('districts/almanac'):
        if name not in district_to_pol: continue  #@@ desynchronized data!
        if 'interest_group_rating' in district:
            for year, groups in district['interest_group_rating'].items():
                for groupname, rating in groups.items():
                    db.insert('interest_group_rating',
                              politician_id=district_to_pol[name],
                              year=year,
                              groupname=groupname,
                              rating=rating)

if __name__ == "__main__": load_all()
