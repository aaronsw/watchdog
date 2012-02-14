import os
import tempfile
import web

production_mode = os.environ.get('PRODUCTION_MODE', False)
render = web.template.render('templates/', base='base', cache=production_mode)
render_plain = web.template.render('templates/', cache=production_mode) #without base, useful for sending mails
if os.environ.get('DATABASE_URL'):
    url = os.environ['DATABASE_URL']
    db = web.database(dbn=url.split(':')[0], user=url.split('//')[1].split(':')[0],
      pw=url.split('@')[0].split(':')[1],
      host=url.split('@')[1].split('/')[0],
      db=url.split('/')[3]
    )
else:
    db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'),
                  db=os.environ.get('WATCHDOG_TABLE', 'watchdog_dev'))
db.printing = False
current_session = '*' # * to load data from all sessions; 'xxx' to load data of that session
