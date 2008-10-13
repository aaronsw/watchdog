import os
import tempfile
import web

render = web.template.render('templates/', base='base')
render_plain = web.template.render('templates/') #without base, useful for sending mails
db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'),
                  db=os.environ.get('WATCHDOG_TABLE', 'watchdog_dev'))
production_mode = os.environ.get('PRODUCTION_MODE', False)
                  
#@@@@ is temp directory really okay for sessions??                  
sess_store = tempfile.mkdtemp()             
session = web.session.Session(None, web.session.DiskStore(sess_store))                  

def setup_session(app):
    app.add_processor(session._processor)
