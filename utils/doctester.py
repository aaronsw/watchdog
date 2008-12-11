#!/usr/bin/python
import doctest, sys
if __name__ == '__main__':
    sys.path.insert(0, '.')
    doctest.testmod(__import__(sys.argv[1]))
