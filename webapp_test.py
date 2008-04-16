#!/usr/bin/python
"Unit tests for code in webapp.py."
import string, re, time
import webapp
import urllib, web

# `request`: Bug-fixed version of `web.application.request`.
# 
# Fixes two bugs in web.application.request:
# 
# 1. the 'path' argument was being handled incorrectly; the 'query'
#    was not being removed from it before it got stuck into PATH_INFO.
# 2. the HTTP headers (I assume that's what they're supposed to be
#    from the name?) were being upcased, but the other parts of the
#    transformation (prepending HTTP_ and turning hyphens into
#    underscores) were not being done.
# 
# I'd fix the bugs in place in web.py, but we haven't checked web.py
# into our Git repository yet, so that would probably result in some
# deployment pain.  So for right now I'm fixing them here.

# Technically maybe `path` should be called `localpart` or
# `path_query` or something.
def request(app, path='/', method='GET', data=None,
            host="0.0.0.0:8080", headers=None, https=False):
    """Makes request to this application for the specified path and method.
    Response will be a storage object with data, status and headers.

        >>> urls = ("/hello", "hello")
        >>> app = application(urls, globals())
        >>> class hello:
        ...     def GET(self): 
        ...         web.header('Content-Type', 'text/plain')
        ...         return "hello"
        ...
        >>> response = app.request("/hello")
        >>> response.data
        'hello'
        >>> response.status
        '200 OK'
        >>> response.headers['Content-Type']
        'text/plain'

    To use https, use https=True.

        >>> urls = ("/redirect", "redirect")
        >>> app = application(urls, globals())
        >>> class redirect:
        ...     def GET(self): raise web.seeother("/foo")
        ...
        >>> response = app.request("/redirect")
        >>> response.headers['Location']
        'http://0.0.0.0:8080/foo'
        >>> response = app.request("/redirect", https=True)
        >>> response.headers['Location']
        'https://0.0.0.0:8080/foo'

    The headers argument specifies HTTP headers as a mapping object
    such as a dict.

    """
    path, maybe_query = urllib.splitquery(path)
    query = maybe_query or ""
    env = dict(HTTP_HOST=host, REQUEST_METHOD=method, PATH_INFO=path, QUERY_STRING=query, HTTPS=https)
    headers = headers or {}
    translation_table = string.maketrans(string.ascii_lowercase + '-',
                                         string.ascii_uppercase + '_')
    for k, v in headers.items():
        env['HTTP_' + string.translate(k, translation_table)] = v

    if data:
        import StringIO
        q = urllib.urlencode(data)
        env['wsgi.input'] = StringIO.StringIO(q)
    response = web.storage()
    def start_response(status, headers):
        response.status = status
        response.headers = dict(headers)
    response.data = "".join(app.wsgifunc()(env, start_response))
    return response

def ok(a, b): assert a == b, (a, b)
def ok_re(a, b): assert re.search(b, a), (a, b)

def test_request():
    "Test our `request` harness."
    urls = ('/ua', 'uaprinter')

    class uaprinter:
        def GET(self):
            return "your user agent is " + web.ctx.env['HTTP_USER_AGENT']

    app = web.application(urls, locals(), autoreload=False)

    ok(request(app, '/ua', headers={
        'User-Agent': 'a small jumping bean/1.0 (compatible)'
    }).data, 'your user agent is a small jumping bean/1.0 (compatible)')

def time_thunk(thunk):
    start = time.time()
    rv = thunk()
    return time.time() - start, rv

def test_find():
    "Test /us/."
    headers = {'Accept': 'text/html'}
    ok(request(webapp.app, '/', headers=headers).status[:3], '200')

    # A ZIP code within a single congressional district.
    resp = request(webapp.app, '/us/?zip=94070', headers=headers)
    ok(resp.status[:3], '303')
    ok(resp.headers.get('Location'), 'http://0.0.0.0:8080/us/ca-12')

    # A ZIP code in Indiana that crosses three districts.
    resp = request(webapp.app, '/us/?zip=46131', headers=headers)
    ok(resp.status[:3], '200')
    ok_re(resp.data, '/us/in-04')
    ok_re(resp.data, 'Stephen Buyer')   # rep for IN-04 at the moment
    ok_re(resp.data, '/us/in-05')
    ok_re(resp.data, '/us/in-06')
    assert '/us/in-07' not in resp.data, resp.data
    
    # Test for LEFT OUTER JOIN: district row with no corresponding politician row.
    resp = request(webapp.app, '/us/?zip=70072', headers=headers)
    ok(resp.status[:3], '200')
    ok_re(resp.data, '/us/la-01')       # no rep at the moment

    # Test for /us/ listing of all the districts and reps.
    # Takes 9-12 seconds on my machine, I think because it's
    # retrieving the district outline data from MySQL.  Takes nearly
    # 1s on watchdog.net.
    reqtime, resp = time_thunk(lambda: request(webapp.app, '/us/',
                                               headers=headers))
    print "took %.3f sec to get /us/" % reqtime
    ok(resp.status[:3], '200')
    ok_re(resp.data, '/us/in-04')
    ok_re(resp.data, 'Stephen Buyer')
    ok_re(resp.data, '/us/la-01')       # LEFT OUTER JOIN test
    assert '(Rep.  )' not in resp.data

def test_state():
    "Test state pages such as /us/nm.html."
    resp = request(webapp.app, '/us/nm.html')
    ok(resp.status[:3], '200')
    ok_re(resp.data, 'href="/us/nm-01"')
    assert '/us/NM-01' not in resp.data # the uppercase URLs aren't canonical
    ok_re(resp.data, 'href="/us/nm-02"')
    ok_re(resp.data, 'href="/us/nm-03"')
    assert '/us/nm-04' not in resp.data

def test_district():
    "Test district pages such as /us/nm-02."
    headers = {'Accept': 'text/html'}
    resp = request(webapp.app, '/us/nm-02', headers=headers)
    ok(resp.status[:3], '200')
    ok_re(resp.data, r'69,598 sq\. mi\.')  # the area

def test_webapp():
    "Test the actual watchdog.net webapp.app app."
    test_find()
    test_state()
    test_district()

def main():
    test_request()
    test_webapp()


if __name__ == '__main__': main()
