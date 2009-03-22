#!/usr/bin/env python
# -*- coding: utf-8 -*-
"Unit tests for code in webapp.py."
import re, time, urllib, pprint, StringIO
import simplejson
import web
from utils import rdftramp
import webapp
import cgitb
cgitb.enable(format='text')

def ok(a, b): assert a == b, (a, b)
def ok_re(a, b): assert re.search(b, a), (a, b)
def ok_items(actual, expected):
    "Check specified keys in a dict."
    for k, v in expected.items(): ok(actual[k], v)

defaultns = rdftramp.Namespace('http://watchdog.net/about/api#')
def ok_graph(actual, expected, ns=defaultns):
    for k, v in expected.items():
        if k == '_type':
            k = rdftramp.rdf.type
            v = ns[v]
        else:
            k = ns[k]
        if isinstance(v, str) and v.startswith('http://'):
            v = rdftramp.URI(v)
        ok(actual[k], v)

def time_thunk(thunk):
    start = time.time()
    rv = thunk()
    return time.time() - start, rv

def json(path):
    "Get and decode JSON for a certain path."
    resp = webapp.app.request(path + '.json')
    ok(resp.status[:3], '200')
    ok(resp.headers['Content-Type'], 'application/json')
    return simplejson.loads(resp.data)

#@@ more places should use this
def html(path):
    resp = webapp.app.request(path, headers={ 'Accept': 'text/html' })
    ok(resp.status[:3], '200')
    assert resp.headers['Content-Type'].startswith('text/html')
    return resp.data

def test_find():
    "Test /us/."
    headers = {'Accept': 'text/html'}
    ok(webapp.app.request('/', headers=headers).status[:3], '200')

    # A ZIP code within a single congressional district.
    resp = webapp.app.request('/us/?zip=94070', headers=headers)
    ok(resp.status[:3], '303')
    ok(resp.headers.get('Location'), 'http://0.0.0.0:8080/us/ca-12')

    # A ZIP code in Indiana that crosses three districts.
    in_zip = html('/us/?zip=46131')
    ok_re(in_zip, '/us/in-04')
    ok_re(in_zip, 'Steve Buyer')   # rep for IN-04 at the moment
    ok_re(in_zip, '/us/in-05')
    ok_re(in_zip, '/us/in-06')
    assert '/us/in-07' not in in_zip, in_zip
    
    # Test for LEFT OUTER JOIN: district row with no corresponding politician row.
    ok_re(html('/us/?zip=70072'), '/us/la-01')       # no rep at the moment

    # Test for /us/ listing of all the districts and reps.
    # Takes 9-12 seconds on my machine, I think because it's
    # retrieving the district outline data from MySQL.  Takes nearly
    # 1s on watchdog.net.
    reqtime, resp = time_thunk(lambda: webapp.app.request('/us/',
                                               headers=headers))
    print "took %.3f sec to get /us/" % reqtime
    ok(resp.status[:3], '200')
    ok_re(resp.data, '/us/in-04')
    ok_re(resp.data, 'Stephen E. Buyer')
    ok_re(resp.data, '/us/la-01')       # LEFT OUTER JOIN test
    assert '(Rep.  )' not in resp.data

    # JSON of /us/ --- very minimal test
    index = json('/us/index')
    ok(len(index), len(list(webapp.db.select('district'))))

def test_state():
    "Test state pages such as /us/nm.html."
    nm = html('/us/nm')
    ok_re(nm, 'href="/us/nm-01"')
    assert '/us/NM-01' not in nm # the uppercase URLs aren't canonical
    ok_re(nm, 'href="/us/nm-02"')
    ok_re(nm, 'href="/us/nm-03"')
    assert '/us/nm-04' not in nm

    # JSON
    resp = webapp.app.request('/us/nm.json')
    ok(resp.status[:3], '200')
    # Copied and pasted from current output; hope it's right.  See
    # below about perils of writing unit tests afterwards.
    nm = simplejson.loads(resp.data)
    ok(len(nm), 1)
    ok_items(nm[0],
        {     'code': 'NM',
          'fipscode': '35',
              'name': 'New Mexico',
            'status': 'state',
             '_type': 'State',
               'uri': 'http://watchdog.net/us/nm#it',
         'wikipedia': 'http://en.wikipedia.org/wiki/New_Mexico',
         'districts': ['http://watchdog.net/us/nm#it', 
                       'http://watchdog.net/us/nm-01#it', 
                       'http://watchdog.net/us/nm-02#it', 
                       'http://watchdog.net/us/nm-03#it']
        })

    # JSON obtained with Accept header.
    rsp2 = webapp.app.request('/us/nm', headers={'Accept': 'application/json'})
    ok(rsp2.data, resp.data)

    #@@ I'd write an N3 test but I'm too sleepy to Google up an N3
    # parser right now.

def test_district():
    "Test district pages such as /us/nm-02."
    nm_02 = html('/us/nm-02')
    ok_re(nm_02, r'69,598\s+sq\. mi\.')  # the district's area
    ok_re(nm_02, 'href=".*/us/nm"')

    # JSON
    (district,) = json('/us/nm-02')
    # I hope these are right.  I just copied them from the current
    # output --- this is a problem with doing unit tests after the
    # fact.  I omitted floating-point numbers (poverty_pct,
    # center_lat, center_lng) and the outline.
    ok_items(district, dict(
        almanac = 'http://nationaljournal.com/pubs/almanac/2008/people/nm/rep_nm02.htm',
        area_sqmi = 69598,
        cook_index = 'R+6',
        est_population = 625204,
        est_population_year = 2005,
        median_income = 29269,
        name = 'NM-02',
        state = 'http://watchdog.net/us/nm#it',
        _type = 'District',
        uri = 'http://watchdog.net/us/nm-02#it',
        wikipedia = "http://en.wikipedia.org/wiki/New_Mexico's_2nd_congressional_district",
        zoom_level = 6,
        voting = True,
    ))

def test_politician():
    (henry,) = json('/p/henry_waxman')  # unpack single item
    henry_dict = dict(
        bioguideid = 'W000215',
        #birthday = '1939-09-12', #@@ looks like at some point we
        # decided to change the format of dates in our JSON? Why?
        district = 'http://watchdog.net/us/ca-30#it',
        firstname = 'Henry',
        gender = 'M',
        lastname = 'Waxman',
        middlename = 'A.',
        officeurl = 'http://www.henrywaxman.house.gov',
        opensecretsid = 'N00001861',
        #party = 'Democrat',             # “Democratic”?
        photo_credit_text = 'Congressional Biographical Directory',
        photo_credit_url =
            'http://bioguide.congress.gov/scripts/bibdisplay.pl?index=W000215',
        religion = 'Jewish',
        _type = 'Politician',
        uri = 'http://watchdog.net/p/henry_waxman#it',
        wikipedia = 'http://en.wikipedia.org/wiki/Henry_Waxman',
        words_per_speech = 1445,
        n_speeches = 8
    )
    ok_items(henry, henry_dict)
    henry_photo_path = '/data/crawl/house/photos/W000215.jpg'
    ok(henry['photo_path'], henry_photo_path)
    henry_govtrackid = '400425'
    ok(henry['govtrackid'], henry_govtrackid)

    #ratings = henry['interest_group_rating']
    #assert dict(year=2006,
    #            groupname='ITIC',
    #            longname='Information Technology Industry Council',
    #            rating=43) in ratings, ratings
    #assert dict(year=2005,
    #            groupname='COC',
    #            longname='Chamber of Commerce of the United States',
    #            rating=38) in ratings, ratings

    #@@ This takes too long now.  I haven’t looked into why.
    if False:
        reqtime, listing = time_thunk(lambda: json('/p/index'))
        print "took %.3f sec to get /p/index.json" % reqtime
        young = [x for x in listing if 
          x['uri'] == 'http://watchdog.net/p/don_young#it'][0]
        ok_items(young, dict(
            district = 'http://watchdog.net/us/ak-00',
            _type = 'Politician',
            uri = 'http://watchdog.net/p/don_young#it',
            wikipedia = 'http://en.wikipedia.org/wiki/Don_Young'
        ))
        ok(listing[-1]['district'], 'http://watchdog.net/us/wy-00')
    
    henry_uri = henry_dict.pop('uri')
    g = rdftramp.Graph()
    g.parse(StringIO.StringIO(webapp.app.request('/p/henry_waxman.n3').data),
            format='n3')
    thing = rdftramp.Thing(rdftramp.URI(henry_uri), g)
    ok_graph(thing, henry_dict)
    #@@ ideally this should be the correct URL, not this file:/// horror
    # (hopefully it’s a correct relative URL in the HTTP interface)
    ok_graph(thing, dict(photo_path=rdftramp.URI('file://' + henry_photo_path)))
    ok_graph(thing, dict(
        govtrackid = 'http://www.govtrack.us/congress/person.xpd?id=' +
        henry_govtrackid))

    g2 = rdftramp.Graph()
    g2.parse(StringIO.StringIO(webapp.app.request('/p/henry_waxman.xml').data),
             format='xml')
    ok_graph(rdftramp.Thing(rdftramp.URI(henry_uri), g2), henry_dict)
    
    # rdflib doesn't support graph equivalence?!
    # http://code.google.com/p/rdflib/issues/detail?id=24
    #assert g == g2
    #@@ probably should test interest group ratings...
    
    ok_re(webapp.app.request('/p/eleanor_holmes_norton').data, "Eleanor Holmes Norton")
    

def test_dproperty():
    page = html('/us/by/est_population')
    montana = re.search('(?s)<li id="dMT-00">(.*)</li>', page)
    assert montana is not None, page
    montana = montana.group(1)
    ok_re(montana, 'href="/us/mt-00">')

def test_blog():
    html('/blog/')

def test_interest_group_table():
    coc = "Chamber of Commerce of the United States"
    aclu = "American Civil Liberties Union"
    ok(webapp.interest_group_table([
        dict(year=2005, groupname='COC', longname=coc, rating=38),
        dict(year=2006, groupname='COC', longname=coc, rating=48),
        dict(year=2006, groupname='ACLU', longname=aclu, rating=80),
        ]), dict(groups=[dict(groupname='ACLU', longname=aclu),
                     dict(groupname='COC', longname=coc)],
                 rows=[
        dict(year=2006, ratings=[80, 48]),
        dict(year=2005, ratings=[None, 38])]))

def test_webapp():
    "Test the actual watchdog.net webapp.app app."
    test_state()
    test_district()
    test_politician()
    test_dproperty()
    test_blog()
    test_find()                         # slow

def main():
    #test_interest_group_table()
    test_webapp()


if __name__ == '__main__': main()

