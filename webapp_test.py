#!/usr/bin/python
"Unit tests for code in webapp.py."
import string, re
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

def test_webapp():
    "Test the actual watchdog.net webapp.app app."
    headers = {'Accept': 'text/html'}
    ok(request(webapp.app, '/', headers=headers).status[:3], '200')

    # A ZIP code in Indiana that crosses three districts.
    resp = request(webapp.app, '/us/?zip=46131', headers=headers)
    ok(resp.status[:3], '200')
    ok_re(resp.data, '/us/in-04')
    ok_re(resp.data, '/us/in-05')
    ok_re(resp.data, '/us/in-06')
    assert '/us/in-07' not in resp.data, resp.data

def main():
    test_request()
    test_webapp()


if __name__ == '__main__': main()
