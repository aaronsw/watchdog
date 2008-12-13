from web.browser import Browser
from webapp import app

test_email = 'testemail@example.com'
test_passwd = 'secret4test'
test_pid = 'test_petition'

def loaddb():
    create_test_user()
    create_test_petition()

def create_test_user():
    from webtest import db
    userexists = db.select('users', where='email=$test_email', vars=dict(test_email=test_email))

    if not userexists:
        b = Browser(app)
        b.open('/u/login')
        b.select_form(name='signup')
        b['email'] = test_email
        b['password'] = b['password_again'] = test_passwd
        res = b.submit()
        assert b.path ==  '/', b.path
        b.open('/c/new')
        assert 'Hi,' in b.data, 'creating test user failed'

def create_test_petition():
    from webtest import db
    petition_exists = db.select('petition', where='id=$test_pid', vars=dict(test_pid=test_pid))
    if not petition_exists:
        b = Browser(app)
        b.open('/c/new')
        b.select_form()
        b['ptitle'] = test_pid.replace('_', ' ')
        b['pid'] = test_pid
        b['msg'] = 'Here is a test petition with a not-so-worthy description, just for testing purpose'
        b.submit()
        assert b.path == '/c/new'
        form = b.select_form(name='login')
        b['useremail'] = test_email
        b['password'] = test_passwd
        b.submit()
        assert 'Congratulations' in b.data, 'creating test petition failed'
        
if __name__ == '__main__':
    loaddb()
