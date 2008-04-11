import Image, ImageDraw, StringIO
import web
from utils import zip2rep

web.config.debug = True
render = web.template.render('templates/', base='base')
db = web.database(dbn='postgres', db='watchdog_dev')

urls = (
  '/', 'index',
  '/us/', 'find',
  '/us/([A-Z][A-Z]-\d+)', 'district',
  '/us/median_income', 'dproperty',
  '/about/', 'about',
  '/images/sparkdist/(.*)', 'sparkdist',
)

class index:
    def GET(self):
        return render.index()

class find:
    def GET(self):
        i = web.input()
        if i.get('zip'):
            dists = zip2rep.zip2dist(i.zip)
            if len(dists) == 1:
                return web.seeother('/us/%s' % dists[0])
            else:
                #@@ need to implement better
                return "multiple districts: " + repr(dists)
                #@@ or no districts...
        else:
            return web.seeother('/')

class district:
    def GET(self, district):
        try:
            d = db.select('district', where='name = $district', vars=locals())[0]
        except IndexError:
            return app.notfound()
        
        return render.district(d)

class dproperty:
    def GET(self):
        maxnum = float(db.select('district', what='max(median_income) as m')[0].m)
        dists = db.select('district', what="*, 100*(median_income/$maxnum) as pct", order='median_income desc', where='median_income is not null', vars=locals())
        return render.dproperty(dists)
        
class about:
    def GET(self):
        return render.about()

class sparkdist:
    def GET(self, what):
        inp = web.input(point=None)
        #@@assert what == 'median_income', 'for security'
        HEIGHT = 15
        WIDTH = 40
        
        BUBBLE = 2
        MARGIN = 5
        SCALEFACTOR = 4
        
        MARGIN *= SCALEFACTOR
        HEIGHT *= SCALEFACTOR
        WIDTH *= SCALEFACTOR
        BUBBLE *= SCALEFACTOR
        
        im = Image.new("RGB", (WIDTH, HEIGHT), 'white')
        HEIGHT -= MARGIN
        WIDTH -= MARGIN
        draw = ImageDraw.Draw(im)
        
        opoints = db.select('district', what=what, order=what+' desc', where=what+' is not null')
        opoints = [x[what] for x in opoints.list()]
        points = [(
          MARGIN/2. + (WIDTH*(n/float(len(opoints)))),
          (HEIGHT+MARGIN/2.) - ((HEIGHT*(float(i)/max(opoints))))
        ) for (n, i) in enumerate(opoints)]
        draw.line(points, fill='#888888', width=1.5*SCALEFACTOR)
        
        if inp.point:
            x, y = points[opoints.index(float(inp.point))]
            draw.ellipse((x-BUBBLE, y-BUBBLE, x+BUBBLE, y+BUBBLE), fill='#f55')        
        
        HEIGHT += MARGIN
        WIDTH += MARGIN
        
        im.thumbnail((WIDTH/SCALEFACTOR, HEIGHT/SCALEFACTOR), Image.ANTIALIAS)
        f = StringIO.StringIO()
        im.save(f, 'PNG')
        
        web.header('Content-Type', 'image/png')
        return f.getvalue()        

app = web.application(urls, globals())
if __name__ == "__main__": app.run()
