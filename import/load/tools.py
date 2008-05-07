"""
common tools for load scripts
"""
import os
import web
db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'), db='watchdog_dev')

_govtrackcache = {}

def govtrackp(govtrack_id):
    """
    Return the watchdog ID for a person's `govtrack_id`.
    
        >>> govtrackp('400114')
        'michael_f._doyle'
        >>> print govtrackp('aosijdoisad') # ID we don't have
        None
    """
    if not _govtrackcache:
        for pol in db.select('politician', what='id, govtrackid'):
            _govtrackcache[pol.govtrackid] = str(pol.id)

    return _govtrackcache.get(govtrack_id)

if __name__ == "__main__":
    import doctest
    doctest.testmod()