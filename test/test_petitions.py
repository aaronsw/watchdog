import webtest
from loaddb import test_email, test_passwd

def fill_captcha(b):
    f = b.select_form()
    for c in f.controls:
        cname = c.name
        if cname and cname.startswith('captcha_') and cname != 'captcha_env':
            c.value = 'xxxxx'

def fill_zip(b, captcha=False):
    f = b.select_form()
    if captcha:
        f['zip5'], f['zip4'], f['state'] = '92003', '0001', ['CA'] #CA-49
        #f['zip5'], f['zip4'], f['state'] = '75101', '0001', ['TX'] #TX-06 for 2 captchas
    else:
        f['zip5'], f['zip4'], f['state'] = '54101', '0011', ['WI'] #WI-08
        
    
class PetitionTest(webtest.TestCase):
    def fill_petition_form(self, f, title, desc, to_congress=False):
        f['ptitle'] = title
        f['pid'] = title.replace(' ', '-')
        f['msg'] = desc
        if to_congress:
            f['tocongress'] = ['on']
            f['prefix'] = ['Mr.']
            f['fname'] = 'Cool'
            f['lname'] = 'Fellow'
            f['addr1'] = '10, Ed St.'
            f['city'] = 'Garden City'
            f['phone'] = '101-100-9999'
            
    def _test_create(self, to_congress=False):
        self.b.open('/c/new')
        form = self.b.select_form()
        self.fill_petition_form(form, 'test petition', 
            'Make the world better place to live!', to_congress=to_congress)

    def test_loggedin_not_to_congress(self):
        """for a logged-in-user, NOT to congress"""
        b = self.browser()
        self.login()
        self._test_create()
        b.submit()
        self.assertEquals(b.path, '/c/test-petition')
        self.assertTrue('Congratulations' in b.data)
        
    def test_not_loggedin_not_to_congress(self):
        """for a NON-logged-in-user, NOT to congress"""
        b = self.browser()
        self._test_create()
        b.submit()
        self.assertEquals(b.path, '/c/new')
        form = b.select_form(name='login')
        b['useremail'] = test_email
        b['password'] = test_passwd
        b.submit()
        self.assertEquals(b.path, '/c/test-petition')
        self.assertTrue('Congratulations' in b.data)

    def test_loggedin_to_congress(self):
        """for a logged-in-user, to congress"""
        b = self.browser()
        self.login()
        self._test_create(to_congress=True)
        fill_zip(b)
        b.submit()
        self.assertEquals(b.path, '/c/test-petition')
        self.assertTrue('Congratulations' in b.data)

    def test_loggedin_to_congress_captcha(self):
        """for a logged-in-user, to congress with a captcha"""
        b = self.browser()
        self.login()
        self._test_create(to_congress=True)
        fill_zip(b, captcha=True)
        b.submit()
        self.assertEquals(b.path, '/c/new')
        #b.show()
        self.assertTrue('Please fill the captcha' in b.data)
        fill_captcha(b)
        b.submit()
        self.assertEquals(b.path, '/c/test-petition')
        self.assertTrue('Congratulations' in b.data)
        
if __name__ == '__main__':
    webtest.main()