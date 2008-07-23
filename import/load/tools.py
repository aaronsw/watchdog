#!/usr/bin/env python
"""
common tools for load scripts
"""
import os
import simplejson
import web
from settings import db

_districtcache = {}
def districtp(district):
    """
    Return the watchdog ID for the represenative of `district`.
    """
    if not _districtcache:
        reps = simplejson.load(file('../data/parse/politicians/index.json'))
        for repid, rep in reps.iteritems():
            _districtcache[rep['district']] = repid
    
    return _districtcache.get(district)

_govtrackcache = {}
_opensecretscache = {}
def _fill():
    for pol in db.select('politician', what='id, govtrackid, opensecretsid'):
        _govtrackcache[pol.govtrackid] = str(pol.id)
        _opensecretscache[pol.opensecretsid] = str(pol.id)
        
def govtrackp(govtrack_id):
    """
    Return the watchdog ID for a person's `govtrack_id`.
    
        >>> govtrackp('400114')
        'michael_f._doyle'
        >>> print govtrackp('aosijdoisad') # ID we don't have
        None
    """
    if not _govtrackcache: _fill()
    return _govtrackcache.get(govtrack_id)

def opensecretsp(opensecrets_id):
    """
    Returns the watchdog ID for a person's `opensecrets_id`.
    """
    if not _opensecretscache: _fill()
    return _opensecretscache.get(opensecrets_id)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
