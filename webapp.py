#!/usr/bin/env python
import os, re
import web
from utils import zip2rep, simplegraphs, apipublish
import blog

web.config.debug = True
web.template.Template.globals['commify'] = web.commify
web.template.Template.globals['int'] = int
render = web.template.render('templates/', base='base')
db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'), db='watchdog_dev')

options = r'(?:\.(html|xml|rdf|n3|json))'
urls = (
  r'/', 'index',
  r'/us/(?:index%s)?' % options, 'find',
  r'/us/([A-Z][A-Z])', 'redistrict',
  r'/us/([a-z][a-z])%s?' % options, 'state',
  r'/us/([A-Z][A-Z]-\d+)', 'redistrict',
  r'/us/([a-z][a-z]-\d+)%s?' % options, 'district',
  r'/us/by/(.*)/distribution.png', 'sparkdist',
  r'/us/by/(.*)', 'dproperty',
  r'/p/(.*?)%s?' % options, 'politician',
  r'/about(/?)', 'about',
  r'/about/api', 'aboutapi',
  r'/about/feedback', 'feedback',
  r'/blog', 'reblog',
  r'/blog(/.*)', blog.app,
  r'/data/(.*)', 'staticdata'
)

class index:
    def GET(self):
        return render.index()

class about:
    def GET(self, endslash=None):
        if not endslash: raise web.seeother('/about/')
        return render.about()

class aboutapi:
    def GET(self):
        return render.about_api()

class feedback:
    def GET(self):
        raise web.seeother('/about')
    
    def POST(self):
        i = web.input(email='info@watchdog.net')
        web.sendmail('Feedback <%s>' % i.email, 'Watchdog <info@watchdog.net>',
          'watchdog.net feedback', 
          i.content +'\n\n' + web.ctx.ip)
        
        return render.feedback_thanks()

class reblog:
    def GET(self):
        raise web.seeother('/blog/')

class find:
    def GET(self, format=None):
        i = web.input(address=None)
        join = ['district' + ' LEFT OUTER JOIN politician '
                             'ON (politician.district = district.name)']
        if i.get('zip'):
            try:
                dists = zip2rep.zip2dist(i.zip, i.address)
            except zip2rep.BadAddress:
                return render.find_badaddr(i.zip, i.address)
            if len(dists) == 1:
                raise web.seeother('/us/%s' % dists[0].lower())
            elif len(dists) == 0:
                return render.find_none(i.zip)
            else:
                dists = db.select(join, where=web.sqlors('name=', dists))
                return render.find_multi(i.zip, dists)
        else:
            out = apipublish.publish([{
              'uri': 'http://watchdog.net/us/' + x.name.lower(),
              'type': 'District',
              'name': x.name,
              'state': x.state,
              'district': x.district,
              'voting': x.voting,
              'wikipedia': apipublish.URI(x.wikipedia)
             } for x in db.select('district')], format)
            if out is not False:
                return out
            
            dists = db.select(join, order='name asc')
            return render.districtlist(dists)

class state:
    def GET(self, state, format=None):
        state = state.upper()
        try:
            state = db.select('state', where='code=$state', vars=locals())[0]
        except IndexError:
            raise web.notfound
        
        out = apipublish.publish(publishify({
          'uri': 'http://watchdog.net/us/' + state.code.lower(),
          'type': 'State',
          'wikipedia': apipublish.URI,
          'code fipscode name status': identity,
        }, [state]), format)
        if out is not False:
            return out
        
        districts = db.select('district',
                              where='state=$state.code',
                              order='district asc',
                              vars=locals())
        
        return render.state(state, districts.list())

class redistrict:
    def GET(self, district):
        return web.seeother('/us/' + district.lower())

#@@ move to web.py?  if so, handle negative numbers and >100 (e.g. 111st)?
def nth_string(n):
    "Format an ordinal.  1 -> 1st, 2 -> 2nd, 3 -> 3rd, 33 -> 33rd, 90 -> 90th."
    assert n >= 0
    if n in [11, 12, 13]: return '%sth' % n
    return {1: '%sst', 2: '%snd', 3: '%srd'}.get(n % 10, '%sth') % n

def publishify(fields, data):
    def publishify_item(fields, datum):
        rv = {}
        for k, v in fields.items():
            for k in k.split():
                if callable(v): rv[k] = v(datum[k])
                else: rv[k] = v
        return rv
    return [publishify_item(fields, datum) for datum in data]

identity = lambda x: x

class district:
    def GET(self, district, format=None):
        try:
            district = district.upper()
            d = db.select(['district', 'state', 'politician'],
                          what=('district.*, '
                                'state.name as state_name, '
                                'politician.firstname as pol_firstname, '
                                'politician.lastname as pol_lastname, '
                                'politician.id as pol_id, '
                                'politician.photo_path as pol_photo_path'),
                          where=('district.name = $district AND '
                                 'district.state = state.code AND '
                                 'politician.district = district.name'),
                          vars=locals())[0]
        except IndexError:
            raise web.notfound
        
        out = apipublish.publish(publishify({
          'uri': 'http://watchdog.net/us/' + district.lower(),
          'type': 'District',
          'state': apipublish.URI('http://watchdog.net/us/' + d.state.lower()),
          'wikipedia almanac': apipublish.URI,
          'name voting area_sqmi cook_index poverty_pct median_income '
          'est_population est_population_year outline center_lat '
          'center_lng zoom_level': identity,
        }, [d]), format)
        if out is not False:
            return out
        
        if d.district == 0:
            d.districtth = 'at-large'
        else:
            d.districtth = nth_string(d.district)
        
        return render.district(d)

class politician:
    def GET(self, polid, format=None):
        if polid != polid.lower():
            raise web.seeother('/p/' + polid.lower())
        
        if polid == "" or polid == "index":
            p = db.select(['politician'], order='district asc').list()
            
            out = apipublish.publish([{
              'uri': 'http://watchdog.net/p/' + x.id,
              'type': 'Politician',
              'district': apipublish.URI('http://watchdog.net/us/' + x.district.lower()),
              'wikipedia': apipublish.URI(x.wikipedia)
             } for x in p], format)
            if out is not False:
                return out
            
            return render.pollist(p)
        
        try:
            p = db.select(['politician', 'district'], what="politician.*, district.center_lat as d0, district.center_lng as d1, district.zoom_level as d2", where='id=$polid AND district.name = politician.district', vars=locals())[0]
        except IndexError:
            raise web.notfound
        
        out = apipublish.publish([{
          'uri': 'http://watchdog.net/p/' + polid,
          'type': 'Politician',
          'district': apipublish.URI('http://watchdog.net/us/' + p.district.lower()),
          'wikipedia': apipublish.URI(p.wikipedia),
          'bioguideid': p.bioguideid,
          'opensecretsid': p.opensecretsid,
          'govtrackid': p.govtrackid,
          'gender': p.gender,
          'birthday': p.birthday,
          'firstname': p.firstname,
          'middlename': p.middlename,
          'lastname': p.lastname,
          'officeurl': p.officeurl,
          'party': p.party,
          'religion': p.religion,
          'photo_path': p.photo_path,
          'photo_credit_url': p.photo_credit_url,
          'photo_credit_text': p.photo_credit_text,
         }], format)
        if out is not False:
            return out
        
        return render.politician(p)

r_safeproperty = re.compile('^[a-z0-9_]+$')

class dproperty:
    def GET(self, what):
        if not r_safeproperty.match(what): raise web.notfound
        
        maxnum = float(db.select('district', what='max(%s) as m' % what, vars=locals())[0].m)
        dists = db.select('district', what="*, 100*(%s/$maxnum) as pct" % what, order='%s desc' % what, where='%s is not null' % what, vars=locals())
        return render.dproperty(dists, what)

class sparkdist:
    def GET(self, what):
        if not r_safeproperty.match(what): raise web.notfound
        
        inp = web.input(point=None)
        points = db.select('district', what=what, order=what+' desc', where=what+' is not null')
        points = [x[what] for x in points.list()]
        
        web.header('Content-Type', 'image/png')
        return simplegraphs.sparkline(points, inp.point)

class staticdata:
    def GET(self, path):
        if not web.config.debug:
            raise web.notfound

        assert '..' not in path, 'security'
        return file('data/' + path).read()

def unit_tests_on_import():
    def ok(a, b): assert a == b, (a, b)
    ok([nth_string(x) for x in [0, 1, 2, 3, 4, 5, 9]],
       "0th 1st 2nd 3rd 4th 5th 9th".split())
    ok([nth_string(x) for x in [10, 20, 21, 100, 102]],
       "10th 20th 21st 100th 102nd".split())
    ok(nth_string(11), "11th")
    ok(nth_string(12), "12th")
    ok(nth_string(13), "13th")
    ok([nth_string(x) for x in [14, 19, 21, 22, 23, 24, 128, 1024]],
       "14th 19th 21st 22nd 23rd 24th 128th 1024th".split())
unit_tests_on_import()

app = web.application(urls, globals())
if __name__ == "__main__": app.run()
