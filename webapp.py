import web
from utils import zip2rep

web.config.debug = True
render = web.template.render('templates/', base='base')
db = web.database(dbn='postgres', db='watchdog_dev')

urls = (
  '/', 'index',
  '/us/', 'find',
  '/us/([A-Z][A-Z]-\d+)', 'district',
  '/about/', 'about'
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
            return web.notfound()
        
        return render.district(d)

class about:
    def GET(self):
        return render.about()

app = web.application(urls, globals())
if __name__ == "__main__": app.run()