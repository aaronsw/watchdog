""" Python library for interacting with Capitol Words API.

    The Capitol Words API (http://www.capitolwords.org/api/) provides access to
    the most commonly used words in Congressional Record each day.
"""

__author__ = "James Turk (jturk@sunlightfoundation.com)"
__version__ = "0.3.0"
__copyright__ = "Copyright (c) 2008 Sunlight Labs"
__license__ = "BSD"

import urllib2
try:
    import json
except ImportError:
    import simplejson as json

class CwodApiError(Exception):
    """ Exception for Capitol Words API errors """

class WordResult(object):
    def __init__(self, d):
        self.__dict__ = d
        if not hasattr(self, 'word_date'):
            self.word_date = None

    def __str__(self):
        if self.word_date:
            return '%s said %s times on %s' % (self.word, self.word_count, self.word_date)
        else:
            return '%s said %s times' % (self.word, self.word_count)

def _get_json(url):
    try:
        response = urllib2.urlopen(url).read()
        return json.loads(response)
    except urllib2.HTTPError, e:
        raise CwodApiError('Invalid Request')
    except ValueError, e:
        raise CwodApiError('Invalid Response')

def _params_to_paramstr(year, month, day, endyear, endmonth, endday):
   # can't specify only part of the range
    if ((endyear or endmonth or endday)
        and not (endyear and endmonth and endday)):
        raise CwodApiError('Invalid number of parameters')

    # join all supplied params together with /s
    params =  (year, month, day, endyear, endmonth, endday)
    paramstr = '/'.join([str(p) for p in params if p])

    if not paramstr:
        paramstr = 'latest'

    return paramstr


def dailysum(word, year, month=None, day=None,
             endyear=None, endmonth=None, endday=None):

    paramstr = _params_to_paramstr(year, month, day, endyear, endmonth, endday)

    # get json
    url = 'http://capitolwords.org/api/word/%s/%s/feed.json' % (word, paramstr)
    result = _get_json(url)
    return [WordResult(r) for r in result]

def wordofday(year=None, month=None, day=None,
              endyear=None, endmonth=None, endday=None, maxrows=1):

    paramstr = _params_to_paramstr(year, month, day, endyear, endmonth, endday)

    url = 'http://capitolwords.org/api/wod/%s/top%s.json' % (paramstr,
                                                             maxrows)
    result = _get_json(url)
    return [WordResult(r) for r in result]


def lawmaker(lawmaker_id, year=None, month=None, day=None,
             endyear=None, endmonth=None, endday=None, maxrows=1):

    paramstr = _params_to_paramstr(year, month, day, endyear, endmonth, endday)

    url = 'http://capitolwords.org/api/lawmaker/%s/%s/top%s.json' % (lawmaker_id,
                                                                     paramstr,
                                                                     maxrows)
    result = _get_json(url)
    return [WordResult(r) for r in result]
