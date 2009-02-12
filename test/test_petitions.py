import webtest
from loaddb import test_email, test_passwd, test_pid, test_pid_to_cong
from utils import messages

def fill_captcha(f):
    for c in f.controls:
        cname = c.name
        if cname and cname.startswith('captcha_') and cname != 'captcha_env':
            c.value = 'xxxxx'

def fill_zip(f, captcha=False):
    if captcha:
        f['zip5'], f['zip4'], f['state'] = '27532', '0001', ['NC'] # NC-03
        #f['zip5'], f['zip4'], f['state'] = '92003', '0001', ['CA'] # CA-49
        #f['zip5'], f['zip4'], f['state'] = '75101', '0001', ['TX'] # TX-06 for 2 captchas
    else:
        f['zip5'], f['zip4'], f['state'] = '54101', '0011', ['WI'] # WI-08
        
def fill_user_details(f, to_congress=False, captcha=False):
    f['fname'] = 'Cool'
    f['lname'] = 'Fellow'
    try:
        e = f.find_control(name='email')
    except:
        pass
    else:
        if e.type != 'hidden': f['email'] = 'cool@fellow.com'
    if to_congress:
        f['prefix'] = ['Mr.']
        f['addr1'] = '10, Ed St.'
        f['city'] = 'Garden City'
        f['phone'] = '101-100-9999'
        fill_zip(f, captcha=captcha)
    
class PetitionTest(webtest.TestCase):
    def fill_petition_form(self, f, title, desc, to_congress=False, captcha=False):
        f['ptitle'] = title
        f['pid'] = title.replace(' ', '-')
        f['msg'] = desc
        if to_congress:
            f['tocongress'] = ['on']
            fill_user_details(f, to_congress, captcha=captcha)

    def _test_create(self, to_congress=False, captcha=False):
        self.b.open('/c/new')
        form = self.b.select_form()
        self.fill_petition_form(form, 'save the world',
            'Make the world better place to live!', to_congress=to_congress, captcha=captcha)

    def _test_L(self, to_congress=False):
        """for a logged-in-user"""
        b = self.browser()
        self.login()
        self._test_create(to_congress=to_congress)
        b.submit()
        self.assertEquals(b.path, '/c/save-the-world')
        self.assertTrue('Congratulations' in b.data)
        return b.data
        
    def _test_NL(self, to_congress=False):
        """for a NON-logged-in-user"""
        b = self.browser()
        self._test_create(to_congress=to_congress)
        b.submit()
        self.assertEquals(b.path, '/c/new')
        form = b.select_form(name='login')
        b['useremail'] = test_email
        b['password'] = test_passwd
        b.submit()
        self.assertEquals(b.path, '/c/save-the-world')
        self.assertTrue('Congratulations' in b.data)
        return b.data

    def test_create_L_NTC(self):
        """for a logged-in-user, NOT to congress"""
        data = self._test_L(to_congress=False)
        self.assertTrue('your comments will be sent to your Representative too.' not in data)

    def test_create_L_TC(self):
        """for a logged-in-user, to congress"""
        data = self._test_L(to_congress=True)
        self.assertTrue('your comments will be sent to your Representative too.' in data)

    def test_create_NL_NTC(self):
        """for a NON-logged-in-user, NOT to congress"""
        data = self._test_NL(to_congress=False)
        self.assertTrue('your comments will be sent to your Representative too.' not in data)

    def test_create_NL_TC(self):
        """for a NON-logged-in-user, to congress"""
        data = self._test_NL(to_congress=True)
        self.assertTrue('your comments will be sent to your Representative too.' in data)

    def test_create_L_TC_captcha(self):
        """for a logged-in-user, to congress with a captcha"""
        b = self.browser()
        self.login()
        self._test_create(to_congress=True, captcha=True)
        b.submit()
        self.assertEquals(b.path, '/c/new')
        self.assertTrue('Please fill the captcha' in b.data)
        f = b.select_form()
        fill_captcha(f)
        b.submit()
        self.assertEquals(b.path, '/c/save-the-world')
        self.assertTrue('Congratulations' in b.data)

    def test_petition_list(self):
        b = self.browser()
        b.open('/c/')
        self.assertTrue(test_pid in b.data)
        self.assertTrue(test_pid_to_cong in b.data)

    def test_edit_by_owner(self):
        b = self.browser()
        self.login()
        b.open('/c/%s/' % test_pid)
        b.follow_link(text='Edit')
        f = b.select_form(name='petition')
        f['msg'] = 'changing the content of the petition' + f['msg']
        b.submit()
        self.assertEquals(b.path, '/c/'+ test_pid)
        self.assertTrue('changing the content of the petition' in b.data)

    def test_edit_by_non_owner(self):
        b = self.browser()
        b.open('/c/%s/?m=edit' % test_pid)
        self.assertTrue(b.path.startswith('/u/login?redirect='))

    def test_delete_by_owner(self):
        b = self.browser()
        self.login()
        self._test_create()
        b.submit()
        b.open('/c/%s/' % 'save-the-world')
        b.follow_link(text='Delete')
        self.assertTrue('Are you sure you want to delete your petition' in b.data)
        b.select_form(name='delete')
        b.submit()
        b.open('/c/save-the-world')
        self.assertEquals(b.status, 404)

class SignTest(webtest.TestCase):
    def make_sign_NL(self, to_congress):
        b = self.browser()
        b.open('/c/%s' % (test_pid_to_cong if to_congress else test_pid))
        f = b.select_form()
        fill_user_details(f, to_congress=to_congress)
        comment = 'a comment here'
        b['comment'] = comment
        b.submit()
        self.assertTrue(b.path.startswith('/share'))
        self.assertTrue('Thanks for your signing' in b.data)
        b.open('/c/%s/signatories' % (test_pid_to_cong if to_congress else test_pid))
        self.assertTrue(comment in b.data)

    def test_sign_NL_NTC(self):
        self.make_sign_NL(to_congress=False)

    def test_sign_NL_TC(self):
        before = len(messages.query().list())
        self.make_sign_NL(to_congress=True)
        after = len(messages.query().list())
        self.assertEquals(before+3, after) # one msg gets added for each rep/sen

    def test_edit_sign(self):
        b = self.browser()
        self.login()
        b.open('/c/%s' % test_pid)
        self.assertTrue('Change your signature' in b.data)
        f = b.select_form(name="sign")
        comment = "I'm the creator of it"
        f['fname'], f['lname'] = 'fname', 'lname'
        f['comment'] = comment 
        b.submit()
        self.assertTrue(b.path.startswith('/share'))
        self.assertTrue('Your signature has been changed' in b.data)
        b.open('/c/%s/signatories' % test_pid)
        self.assertTrue(comment in b.data)

if __name__ == '__main__':
    webtest.main()
