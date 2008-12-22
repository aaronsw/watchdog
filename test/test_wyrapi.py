import webtest
import simplejson
from utils.api import app as apiapp

class WYRAPI_TEST(webtest.TestCase):
    def request(self, path):
        response = apiapp.request(path)
        self.assertEquals(response.status[:3], '200')
        self.assertEquals(response.headers['Content-Type'], 'application/json')
        return simplejson.loads(response.data)

    def test_prepare(self):
        data = self.request("/wyr.prepare?district=WI-01")
        for pol in data:
            self.assertEquals(data[pol]['captcha_src'], None)

    def test_prepare_captcha(self):
        data = self.request("/wyr.prepare?district=TX-01")
        captcha_src = None
        for pol in data:
            captcha_src = captcha_src or data[pol]['captcha_src']
        self.assertTrue(captcha_src)

    def test_prepare_wrong_input(self):
        data = self.request("/wyr.prepare?zip5=00000&zip4=1111")
        self.assertEquals(data.get('err_msg'), 'Invalid zip and/or address' )

        data = self.request("/wyr.prepare?district=AA-01")
        self.assertEquals(data.get('err_msg'), 'Invalid district')

    def test_send(self):
        pass

    def test_send_captcha(self):
        pass    

if __name__ == '__main__':
    webtest.main()    
