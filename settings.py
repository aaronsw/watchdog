import os
import tempfile
import web

render = web.template.render('templates/', base='base')
db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'),
                  db=os.environ.get('TABLE_NAME', 'watchdog_dev'))
                  
#@@@@ is temp directory really okay for sessions??                  
sess_store = tempfile.mkdtemp()             
session = web.session.Session(None, web.session.DiskStore(sess_store))                  

def setup_session(app):
    app.add_processor(session._processor)

