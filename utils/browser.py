"""
Browser: maintains state across multiple urlopens
"""

import urllib2, cookielib
from BeautifulSoup import BeautifulSoup
from ClientForm import ParseFile, ParseError, XHTMLCompatibleFormParser
from StringIO import StringIO

class Browser:
    def __init__(self, state=None):
        self.cp = urllib2.HTTPCookieProcessor()
        self.page = None
        self.url = None
        if state: self.set_state(state)
        
    def get_state(self):
        return [self._dump_cookie(c) for c in self._get_cookies(self.cp.cookiejar)]
      
    def set_state(self, state):
        cookies = state
        self._set_cookies(self.cp.cookiejar, [self._load_cookie(d) for d in cookies])
        
    def open(self, request, data=None):
        """opens the url or processes the request and returns the response"""
        response = urllib2.build_opener(self.cp).open(request, data)
        self.page = response.read()
        self.url = response.geturl()
        return self.page
        
    def get_forms(self, predicate=None):
        """Returns all the forms satisfying predicate."""
        try:
            forms = ParseFile(StringIO(self.page), self.url, backwards_compat=False)
        except ParseError:
            forms = ParseFile(StringIO(self.page), self.url, backwards_compat=False, \
                    form_parser_class=XHTMLCompatibleFormParser)
        return (f for f in forms if predicate is None or predicate(f))
    
    def get_form(self, predicate):
        try:
            return self.get_forms(predicate).next()
        except StopIteration:
            pass    
    
    def get_text(self):
        soup = BeautifulSoup(self.page)
        return ''.join(e.strip() for e in soup.recursiveChildGenerator() if isinstance(e, unicode))
    
    def has_text(self, msg):
        text = self.get_text()
        return msg.lower() in text.lower()
        
    def find_nodes(self, tags, predicate=None, attrs={}):
        """Finds matching nodes from the current page"""
        soup = BeautifulSoup(self.page)
        return [n for n in soup.findAll(tags, attrs) if predicate is None or predicate(n)]
        
    def _get_cookies(self, cookiejar):
        """returns all cookies in the cookiejar."""
        for domain, domain_cookies in cookiejar._cookies.items():
            for path, path_cookies in domain_cookies.items():
                for name, cookie in path_cookies.items():
                    yield cookie   

    def _dump_cookie(self, cookie):
        """convert a cookie to a dictionary."""
        d = dict(cookie.__dict__)
        d['rest'] = d.pop('_rest')
        return d

    def _set_cookies(self, cookiejar, cookies):
        """adds the given cookies to the cookie jar."""
        for cookie in cookies:
            cookiejar.set_cookie(cookie)

    def _load_cookie(self, data):
        """Creates a cookie from the dumped dict."""
        d = dict( [(str(k), v) for (k, v) in data.items()]) #keys are getting unicode values somewhere
        return cookielib.Cookie(**d)

