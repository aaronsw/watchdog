import urllib, pickle, os, sys
import simplejson as json

def listify(x):
    if not isinstance(x, list):
        return [x]
    else:
        return x

def jsonify(d):
    return json.dumps(d, indent=2, sort_keys=True)

def cachejson(funct):
    name = funct.__name__
    if name.startswith('get'): name = name[len('get'):]
    content = funct()
    
    fh = file('%s.json' % name, 'w')
    fh.write(jsonify(content))
    fh.close()

def uncachejson(name):
    return json.load(file('%s.json' % name))

PVS_API_KEY = file('.pvsapikey.secret').read().strip()
PVS_URL = 'http://api.votesmart.org/%s?%s&key=%s&o=JSON'
PVS_EMPTY = [
  'No districts found fitting this criteria.',
  'No candidates found in this district.',
  'No active officials found in this district.',
  'No candidates for this ID or no additional bio data.',
  'No categories for this state and year.',
  'No Ratings fit this criteria.',
  'Campaign address no longer available or candidate does not exist.',
  'Office address no longer available or candidate does not exist.',
  'Office Web address no longer available or candidate does not exist.',
  'Campaign Web address no longer available or candidate does not exist.']

def pvs(cmd, **attrs):
    u = PVS_URL % (cmd, urllib.urlencode(attrs), PVS_API_KEY)
    d = urllib.urlopen(u)
    return json.load(d)

def pvsexists(d):
    if d.get('error') and d['error']['errorMessage'] in PVS_EMPTY:
        return False
    else:
        return d

def getstates():
    out = {}
    for state in pvs('State.getStateIDs')['stateList']['list']['state']:
        out[state.pop('stateId')] = state
    return out

# cachejson(getstates)

def getdistricts():
    out = {}
    for state in uncachejson('states').keys():
        d = pvs('District.getByOfficeState', officeId=5, stateId=state)
        if pvsexists(d):
            for x in listify(d['districtList']['district']):
                assert x.pop('officeId') == '5'
                cdist = x.pop('stateId') + '-' 
                cdist2 = x['name'].split(' ')[-1]
                if cdist2.isdigit():
                    cdist += cdist2.zfill(2)
                elif cdist2 in ['At-Large', 'Delegate', 'Commissioner']:
                    cdist += '00'
                else:
                    print d
                    raise ValueError, cdist2
                out[cdist] = x

        d = pvs('District.getByOfficeState', officeId=6, stateId=state)
        if pvsexists(d):
            for x in listify(d['districtList']['district']):
                assert x.pop('officeId') == '6'
                cdist = x.pop('stateId') + '-'
                if x['name'].startswith('Senior'):
                    cdist += 'SEN1'
                else:
                    cdist += 'SEN2'
                out[cdist] = x
    return out

def getcandidates():
    out = {}
    db = uncachejson('districts')
    for districtid, district in db.iteritems():
        sys.stderr.write('\r' + districtid.ljust(10))
        sys.stderr.flush()
        d = pvs('Officials.getByDistrict', districtId=district['districtId'])
        if pvsexists(d):
            for c in listify(d['candidateList']['candidate']):
                out.setdefault(districtid, [])
                out[districtid].append(c)

        d = pvs('Candidates.getByDistrict', districtId=district['districtId'])
        if pvsexists(d):
            for c in listify(d['candidateList']['candidate']):
                out.setdefault(districtid, [])
                out[districtid].append(c)
    return out

def getbios():
    out = {}
    for district in uncachejson('candidates').itervalues():
        for can in district:
            if can['candidateId'] in out: continue
            print can['firstName'], can['lastName']
            d = pvs('CandidateBio.getBio', candidateId=can['candidateId'])
            d2 = pvs('CandidateBio.getAddlBio', candidateId=can['candidateId'])
            if pvsexists(d2) and d2['addlbio']['additional']:
                d['bio']['additional'] = listify(d2['addlbio']['additional']['item'])
            out[can['candidateId']] = d['bio']
    return out

def getratingcategories():
    out = {}
    for state in uncachejson('states').keys():
        d = pvs('Rating.getCategories', stateId=state)
        if pvsexists(d):
            out[state] = listify(d['categories']['category'])
    return out

def getsigcategories():
    out = {}
    for state, cats in uncachejson('ratingcategories').iteritems():
        for cat in cats:
            d = pvs('Rating.getSigList', categoryId=cat['categoryId'], stateId=state)
            for sig in listify(d['sigs']['sig']):
                sig['categoryId'] = cat['categoryId']
                sig['stateId'] = state
                out[sig['sigId']] = sig
    return out

def getsigs():
    out = {}
    for sig in uncachejson('sigcategories').itervalues():
        if sig['sigId'] in out: continue
        d = pvs('Rating.getSig', sigId=sig['sigId'])
        del d['sig']['generalInfo']
        out[sig['sigId']] = d['sig']
    return out

def getratings():
    sigs = [x for x in uncachejson('sigs').values() if x['stateId'] == 'NA']
    cans = sum(uncachejson('candidates').values(), [])
    
    fh = file('ratings.json.netstrings', 'w')
    
    n = 0
    total = len(sigs) * len(cans)
    for can in cans:
        for sig in sigs:
            n += 1
            sys.stderr.write('\r%s / %s = %s' % (n, total, float(n)/total))
            sys.stderr.flush()
            d = pvs('Rating.getCandidateRating', candidateId=can['candidateId'], sigId=sig['sigId'])
            if pvsexists(d):
                out = jsonify({
                  'sigId': sig['sigId'], 
                  'candidateId': can['candidateId'],
                  'ratings': listify(d['candidateRating']['rating'])
                })
                
                fh.write('%s:%s' % (len(out), out))
        fh.flush()
    return out

def parsenetstrings(fh):
    while True:
        n = []
        n.append(fh.read(1))
        if n[-1] == '': break # we're done
        while n[-1].isdigit():
            n.append(fh.read(1))
        assert n[-1] == ':'
        yield fh.read(int(''.join(n[:-1])))

def parseratings():
    for string in parsenetstrings(file('ratings.json.netstrings')):
        yield json.loads(string)

def getoffices():
    out = {}
    cans = sum(uncachejson('candidates').values(), [])
    
    for n, can in enumerate(cans):
        d = pvs('Address.getOffice', candidateId=can['candidateId'])
        d2 = pvs('Address.getCampaign', candidateId=can['candidateId'])
        sys.stderr.write('\r%s / %s = %s' % (n, len(cans), float(n)/len(cans)))
        sys.stderr.flush()
        o = out[can['candidateId']] = {}
        if pvsexists(d):
            o['office'] = listify(d['address']['office'])
        if pvsexists(d2):
            o['campaign'] = listify(d2['address']['office'])
    return out

def getwebsites():
    out = {}
    
    cans = sum(uncachejson('candidates').values(), [])
    for n, can in enumerate(cans):
        d = pvs('Address.getOfficeWebAddress', candidateId=can['candidateId'])
        d2 = pvs('Address.getCampaignWebAddress', candidateId=can['candidateId'])
        sys.stderr.write('\r%s / %s = %s' % (n, len(cans), float(n)/len(cans)))
        sys.stderr.flush()
        o = out[can['candidateId']] = {}
        if pvsexists(d):
            o['office'] = listify(d['webaddress']['address'])
        if pvsexists(d2):
            o['campaign'] = listify(d2['webaddress']['address'])
    return out

def getnpat():
    out = {}
    cans = sum(uncachejson('candidates').values(), [])
    
    for can in cans:
        d = pvs('Npat.getNpat', candidateId=can['candidateId'])
        if d.get('error'):
            if d['error']['errorMessage'] == 'Unknown error': continue            
            print d
            continue
        out[can['candidateId']] = d
    
    return out

def webproxy():
    import web, pprint
    urls = ('/(.*)', 'main')
    class main:
        def GET(self, url):
            pprint.pprint(pvs(url, **web.input()))

    web.run(urls, locals())

if __name__ == "__main__":
    cachejson(getstates)
    cachejson(getdistricts)
    cachejson(getcandidates)
    cachejson(getbios)
    cachejson(getoffices)
    cachejson(getwebsites)
    cachejson(getnpat)
