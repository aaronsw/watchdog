import webtest
from loaddb import test_email, test_passwd
from test_petitions import fill_user_details, fill_captcha

class WYRTest(webtest.TestCase):
    def _fill_wyr_form(self, f, subject, msg, captcha=False):
        fill_user_details(f, to_congress=True, captcha=captcha)
        f['ptitle'] = subject
        f['msg'] = msg
            
    def _create_msg(self, captcha=False):
        subject = 'Test subject'
        msg = 'Test msg'
        b = self.browser()
        b.open('/writerep/')
        f = b.select_form(name='writerep')
        self._fill_wyr_form(f, subject, msg, captcha=captcha)
        return b
                
    def test_no_captcha(self):
        b = self._create_msg()
        b.submit()
        self.assertEquals(b.path, '/writerep/')
        self.assertTrue('Your message has been sent to ' in b.data)
        
    def test_captcha(self):
        b = self._create_msg(captcha=True)
        b.submit()
        self.assertTrue('Please fill the captcha' in b.data)
        f = b.select_form(name='writerep')
        fill_captcha(f)
        b.submit()
        self.assertEquals(b.path, '/writerep/')
        self.assertTrue('Your message has been sent to ' in b.data)
        
    def test_incomplete_details(self):
        b = self._create_msg()
        f = b.select_form()
        f['zip5'] = '' #take off zip
        b.submit()
        self.assertTrue('Please try again after fixing the errors highlighted below')
        f = b.select_form(name='writerep')
        fill_user_details(f, to_congress=True)
        b.submit()
        self.assertEquals(b.path, '/writerep/')
        self.assertTrue('Your message has been sent to' in b.data)

if __name__ == "__main__":
    webtest.main()
