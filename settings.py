import os
import web

render = web.template.render('templates/', base='base')
db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'),
                  db='watchdog_dev')
