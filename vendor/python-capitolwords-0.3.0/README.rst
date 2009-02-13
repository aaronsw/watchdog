===================
python-capitolwords
===================

Python library for interacting with Capitol Words API.

Capitol Words provides access to the most commonly used words in Congressional 
Record each day. (http://www.capitolwords.org/api/)

python-capitolwords is a project of Sunlight Labs (c) 2009
Written by James Turk <jturk@sunlightfoundation.com>.

All code is under a BSD-style license, see LICENSE for details.

Homepage: http://pypi.python.org/pypi/python-capitolwords/

Source: http://github.com/sunlightlabs/python-capitolwords/


Requirements
============

python >= 2.4

simplejson >= 1.8 (not required with python 2.6, will use built in json module)


Installation
============
To install run

    ``python setup.py install``

which will install the bindings into python's site-packages directory.

Usage
=====

All that is required to start using the API is for it to be imported, no API key is
required for Capitol Words.

Import ``capitolwords``:
    
    >>> import capitolwords
    
All Capitol Words API methods return a WordResult object with three attributes:
    * word          - a word in question
    * word_date     - a particular date **[not available for lawmaker]**
    * word_count    - the number of times ``word`` was said

dailysum
--------

``dailysum(word, year, month=None, day=None, endyear=None, endmonth=None, endday=None)``

dailysum returns a list of records given a word and a series of days.

Using ``dailysum`` to find out how many times 'transparency' was said on
May 22nd 2008:

    >>> wr = capitolwords.dailysum('transparency', 2008, 5, 22)[0]
    >>> print wr.word_count
    47

Using ``dailysum`` to find out how many times 'transparency' was said
in May 2008:

    >>> for wr in capitolwords.dailysum('transparency', 2008, 5):
    ...     print wr.word_date, wr.word_count
    2008-05-23 3
    2008-05-22 47
    2008-05-21 13
    2008-05-20 18
    2008-05-19 25
    2008-05-15 22
    2008-05-14 22
    2008-05-13 17
    2008-05-12 10
    2008-05-08 8
    2008-05-07 11
    2008-05-06 6
    2008-05-05 1
    2008-05-02 1
    2008-05-01 11

Using ``dailysum`` to find out how many times 'transparency' was said
for all days in a given range of days:

    >>> for wr in capitolwords.dailysum('transparency', 2008, 4, 3, 2008, 4, 10):
    ...     print wr.word_date, wr.word_count
    2008-04-10 2
    2008-04-09 8
    2008-04-08 5
    2008-04-07 4
    2008-04-03 8

wordofday
---------

``dailysum(year=None, month=None, day=None, endyear=None, endmonth=None, endday=None, maxrows=1)``

wordofday returns a list of records representing the most commonly used words for given dates.

Using ``wordofday`` to get the top 5 words for April 3rd, 2008:

    >>> for w in capitolwords.wordofday(2008, 4, 3, maxrows=5):
    ...     print w.word, w.word_count
    sergeant 1706
    housing 1382
    director 976
    corporal 899
    mortgage 868

Using ``wordofday`` to get the top words for every day in May 2008:

    >>> for w in capitolwords.wordofday(2008, 5):
    ...     print w.word, w.word_count, w.word_date
    conrad 3 2008-05-29
    recess 3 2008-05-27
    name 146 2008-05-23
    defense 2411 2008-05-22
    tax 1109 2008-05-21
    assistance 1004 2008-05-20
    assistance 645 2008-05-19
    food 40 2008-05-16
    iraq 586 2008-05-15
    budget 756 2008-05-14
    assistance 1402 2008-05-13
    oil 546 2008-05-12
    housing 1418 2008-05-08
    insurance 591 2008-05-07
    insurance 631 2008-05-06
    day 95 2008-05-05
    housing 82 2008-05-02
    health 879 2008-05-01

Using ``wordofday`` to get the word of day across a given range:

    >>> for w in capitolwords.wordofday(2008, 4, 3, 2008, 4, 10):
    ...     print w.word, w.word_count, w.word_date
    energy 465 2008-04-10
    health 380 2008-04-09
    energy 265 2008-04-08
    housing 540 2008-04-07
    energy 244 2008-04-04
    sergeant 1706 2008-04-03


lawmaker
--------

``lawmaker(lawmaker_id, year=None, month=None, day=None, endyear=None, endmonth=None, endday=None, maxrows=1)``

lawmaker returns a list of records representing a lawmakers most said words

lawmakers are referenced by their `Bioguide ID`_.  Bioguide IDs can be obtained from the `Sunlight Labs API`_.

**[Note: the word_date attribute of the records is not populated as it does not apply to this method]**

Using ``lawmaker`` to get the words Mitch McConnell said the most on October 10th, 2008:

    >>> for w in capitolwords.lawmaker('M000355', 2008, 12, 12, maxrows=5):
    ...     print w.word, w.word_count
    dole 23
    women 16
    elizabeth 13
    included 11
    north 11

Using ``lawmaker`` to get the words Mitch McConnell said the most across a given range:

    >>> for w in capitolwords.lawmaker('M000355', 2008, 4, 3, 2008, 4, 10, maxrows=5):
    ...     print w.word, w.word_count
    lance 24
    home 21
    iraq 21
    colombia 19
    nominee 17

.. _`Bioguide ID`: http://bioguide.congress.gov/
.. _`Sunlight Labs API`: http://services.sunlightlabs.com/api/
