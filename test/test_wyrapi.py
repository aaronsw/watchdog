import webtest
import simplejson
import urllib
from utils.api import app as apiapp

user_data = dict(prefix='Mr.', lname='lastname', fname='firstname', district='WI-01', 
            address='10, North Road', phone='123456789',
            zip5='53101', zip4='0001', city='Garden city',
            subject='hello', msg='just to say hello', env={})

class WYRAPI_TEST(webtest.TestCase):
    def request(self, path, data=None):
        b = self.browser()
        response = b.open(path, data)
        self.assertEquals(response.headers['Content-Type'], 'application/json')
        return simplejson.loads(response.read())

    def test_prepare(self):
        data = self.request('/api/wyr.prepare?district=WI-01')
        for pol in data:
            self.assertEquals(data[pol]['captcha_src'], None)

    def test_prepare_captcha(self):
        data = self.request('/api/wyr.prepare?district=CA-49')
        captcha_src = None
        for pol in data:
            captcha_src = captcha_src or data[pol]['captcha_src']
        self.assertTrue(captcha_src)

    def test_prepare_wrong_input(self):
        data = self.request('/api/wyr.prepare?zip5=00000&zip4=1111')
        self.assertEquals(data.get('err_msg'), 'Invalid zip and/or address' )

        data = self.request('/api/wyr.prepare?district=AA-01')
        self.assertEquals(data.get('err_msg'), 'Invalid district')

    def test_send(self):
        udata_dict = user_data.copy()
        udata = urllib.urlencode(udata_dict)
        prepared_data = self.request('/api/wyr.prepare?%s' % udata)
        udata_dict['env'] = simplejson.dumps(prepared_data)
        data = self.request('/api/wyr.send', udata)
        for pol in data:
            self.assertEquals(data[pol]['status'], 'SENT')
            self.assertTrue(data[pol]['msgid'])

    def test_send_wrong_input(self):
        udata = user_data.copy()
        del udata['lname']
        udata = urllib.urlencode(udata)
        data = self.request('/api/wyr.send', udata)
        self.assertTrue('err_msg' in data)
        self.assertEquals(data['err_msg'], 'Invalid Last Name')
            
    def test_send_captcha(self):
        udata_dict = user_data.copy()
        udata_dict['district'] = 'CA-49'
        udata_dict['zip5'], udata_dict['zip4'] = '92003', '0001'
        udata = urllib.urlencode(udata_dict)
        prepared_data = self.request('/api/wyr.prepare?%s' % udata)

        #send without filling captcha value and get error
        udata_dict['env'] = simplejson.dumps(prepared_data)
        send_data = urllib.urlencode(udata_dict)
        data = self.request('/api/wyr.send', send_data)
        self.assertEquals(data['err_msg'], 'Invalid captcha value')
        
        #fill captcha value and succeed in sending
        for pol in prepared_data:
            prepared_data[pol]['captcha_value'] = 'something'

        udata_dict['env'] = simplejson.dumps(prepared_data)
        send_data = urllib.urlencode(udata_dict)
        data = self.request('/api/wyr.send', send_data)
        
        for pol in data:
            self.assertEquals(data[pol]['status'], 'SENT')
            self.assertTrue(data[pol]['msgid'])

if __name__ == '__main__':
    webtest.main()    
