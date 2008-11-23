#!/usr/bin/env python
"""
common tools for parsers
"""

import sys
import simplejson as json

def netstring(x):
    """
        >>> netstring('banana')
        '6:banana,'
    """
    return str(len(x)) + ':' + x + ','

def jsonify(d):
    return json.dumps(d, indent=2, sort_keys=True)

def export(generator):
    for item in generator:
        sys.stdout.write(netstring(jsonify(item)))

def unexport(fh):
    n = '0'
    while n:
        n = int(n + ''.join(c for c in iter(lambda: fh.read(1), ':')))
        yield json.loads(fh.read(n))
        assert fh.read(1) == ','
        n = fh.read(1)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
