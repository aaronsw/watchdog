#!/usr/bin/python
import os, re
import web
from utils import zip2rep, simplegraphs
import blog

web.config.debug = True
web.template.Template.globals['commify'] = web.commify
render = web.template.render('templates/', base='base')
db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'), db='watchdog_dev')

urls = (
  '/', 'index',
  '/us/', 'find',
  '/us/([A-Z][A-Z])', 'redistrict',
  '/us/([a-z][a-z])', 'state',
  '/us/([A-Z][A-Z]-\d+)', 'redistrict',
  '/us/([a-z][a-z]-\d+)', 'district',
  '/us/by/(.*)/distribution.png', 'sparkdist',
  '/us/by/(.*)', 'dproperty',
  '/p/(.*)', 'politician',
  '/about(/?)', 'about',
  '/about/feedback', 'feedback',
  '/blog', 'reblog',
  '/blog(/.*)', blog.app,
  '/data/(.*)', 'staticdata'
)

class index:
    def GET(self):
        return render.index()

class about:
    def GET(self, endslash=None):
        if not endslash: raise web.seeother('/about/')
        return render.about()

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
    def GET(self):
        i = web.input(address=None)
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
                dists = db.select(['district', 'politician'], where=web.sqlors('name=', dists) + ' AND politician.district = district.name')
                return render.find_multi(i.zip, dists)
        else:
            return web.seeother('/')

class state:
    def GET(self, state):
        state = state.upper()
        try:
            state = db.select('state', where='code=$state', vars=locals())[0]
        except IndexError:
            raise web.notfound
        districts = db.select('district', where='state=$state.code', order='district asc', vars=locals())
        
        return render.state(state, districts.list())

class redistrict:
    def GET(self, district):
        return web.seeother('/us/' + district.lower())

class district:
    def GET(self, district):
        try:
            district = district.upper()
            d = db.select(['district', 'state', 'politician'], what='district.*, state.name as state_name, politician.firstname as pol_firstname, politician.lastname as pol_lastname, politician.id as pol_id, politician.photo_path as pol_photo_path', where='district.name = $district AND district.state = state.code AND politician.district = district.name', vars=locals())[0]
        except IndexError:
            raise web.notfound
        
        if d.district == 0:
            d.districtth = 'at-large'
        elif str(d.district).endswith('1'):
            d.districtth = '%sst' % d.district
        elif str(d.district).endswith('2'):
            d.districtth = '%snd' % d.district
        elif str(d.district).endswith('3'):
            d.districtth = '%srd' % d.district
        else:
            d.districtth = '%sth' % d.district
        
        return render.district(d)

class politician:
    def GET(self, polid):
        if polid != polid.lower():
            raise web.seeother('/p/' + polid.lower())
        
        p = db.select(['politician', 'district'], what="politician.*, district.center_lat as d0, district.center_lng as d1, district.zoom_level as d2", where='id=$polid AND district.name = politician.district', vars=locals())[0]
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

app = web.application(urls, globals())
if __name__ == "__main__": app.run()
