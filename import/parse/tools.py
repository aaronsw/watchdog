#!/usr/bin/env python
"""
common tools for parsers
"""

import sys
import simplejson

def netstring(x):
    """
        >>> netstring('banana')
        '6:banana,'
    """
    return str(len(x)) + ':' + x + ','

def jsonify(d):
    return simplejson.dumps(d, indent=2, sort_keys=True)

def export(generator):
    for item in generator:
        sys.stdout.write(netstring(jsonify(item)))

if __name__ == "__main__":
    import doctest
    doctest.testmod()