#!/usr/bin/python
import os, re
import web
from utils import zip2rep, simplegraphs
import blog

web.config.debug = True
render = web.template.render('templates/', base='base')
db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'), db='watchdog_dev')

urls = (
  '/', 'index',
  '/us/', 'find',
  '/us/([A-Z][A-Z]-\d+)', 'redistrict',
  '/us/([a-z][a-z]-\d+)', 'district',
  '/us/by/(.*)/distribution.png', 'sparkdist',
  '/us/by/(.*)', 'dproperty',
  '/p/(.*)', 'politician',
  '/about(/?)', 'about',
  '/about/feedback', 'feedback',
  '/blog', 'reblog',
  '/blog(/.*)', blog.app,
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
        i = web.input()
        if i.get('zip'):
            dists = zip2rep.zip2dist(i.zip)
            if len(dists) == 1:
                raise web.seeother('/us/%s' % dists[0].lower())
            else:
                #@@ need to implement better
                return "multiple districts: " + repr(dists)
                #@@ or no districts...
        else:
            return web.seeother('/')

class redistrict:
    def GET(self, district):
        return web.seeother('/us/' + district.lower())

class district:
    def GET(self, district):
        try:
            district = district.upper()
            d = db.select(['district', 'state', 'politician'], what='district.*, state.name as state_name, politician.firstname as pol_firstname, politician.lastname as pol_lastname, politician.id as pol_id', where='district.name = $district AND district.state = state.code AND politician.district = district.name', vars=locals())[0]
        except IndexError:
            raise web.notfound
        
        return render.district(d)

class politician:
    def GET(self, polid):
        if polid != polid.lower():
            raise web.seeother('/p/' + polid.lower())
        
        p = db.select(['politician', 'district'], what="politician.*, district.outline as district_outline", where='id=$polid AND district.name = politician.district', vars=locals())[0]
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

app = web.application(urls, globals())
if __name__ == "__main__": app.run()
