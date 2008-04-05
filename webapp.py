import web

web.config.debug = True
render = web.template.render('templates/', base='base')
db = web.database(dbn='postgres', db='watchdog_dev', user='postgres', pw='')

urls = (
  '/', 'index',
  '/us/([A-Z][A-Z]-\d+)', 'district',
)

class index:
    def GET(self):
        return render.index()

class district:
    def GET(self, district):
        try:
            d = db.select('district', where='name = $district', vars=locals())[0]
        except IndexError:
            return web.notfound()
        
        return render.district(d)

app = web.application(urls, globals())
if __name__ == "__main__": app.run()