"""
Utils for xapian.
"""
try:
    import xappy
except ImportError:
    import warnings
    warnings.warn('No xappy found. Skipping search engine stuff.')
    def query(s):
        return []

DBPATH = 'se'

def query(s):
    sconn = xappy.SearchConnection(DBPATH)
    q = sconn.query_parse(sconn.spell_correct(s), default_op=sconn.OP_AND)
    return [x.data['id'][0] for x in sconn.search(q, 0, 10)]
