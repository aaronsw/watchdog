import webtest
from loaddb import test_email, test_passwd

class LoginTest(webtest.TestCase):
    def testRegister(self):
        b = self.browser()
        b.open('/u/login')
        b.select_form(name='signup')
        b['email'] = 'user@example.com'
        b['password'] = b['password_again'] = 'secret'
        res = b.submit()
        self.assertEquals(b.path, '/')

    def testRegister_diff_passwds(self):
        b = self.browser()
        b.open('/u/login')
        b.select_form(name='signup')
        b['email'] = 'user@example.com'
        b['password'] = 'secret'
        b['password_again'] = 'different'
        res = b.submit()
        self.assertEquals(b.path, '/u/signup')
        assert "Oops, passwords don&#39;t match" in b.data

    def testRegister_user_exists(self):
        b = self.browser()
        b.open('/u/login')
        b.select_form(name='signup')
        b['email'] = test_email
        b['password'] = 'anything'
        b['password_again'] = 'anything'
        b.submit()
        self.assertEquals(b.path, '/u/signup')
        assert "An account with that email already exists" in b.data

    def testLogin(self):
        b = self.browser()
        b.open('/u/login')
        b.select_form(name='login')
        b['useremail'] = test_email
        b['password'] = test_passwd
        b.submit()
        self.assertEquals(b.path, '/')

    def testLogin_wrong_passwd(self):
        b = self.browser()
        b.open('/u/login')
        b.select_form(name='login')
        b['useremail'] = test_email
        b['password'] = test_passwd + '@@@@'
        b.submit()
        self.assertEquals(b.path, '/u/login')
        assert 'Oops, wrong email or password' in b.data

    def testLogin_no_user_exist(self):
        b = self.browser()
        b.open('/u/login')
        b.select_form(name='login')
        b['useremail'] = test_email + 'extra'
        b['password'] = test_passwd
        b.submit()
        self.assertEquals(b.path, '/u/login')
        assert 'No account exists with this email' in b.data
        
if __name__ == "__main__":
    webtest.main()
