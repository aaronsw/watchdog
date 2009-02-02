#!/usr/bin/python
"""Print out the contents of a pickle file.

Since I started writing pickle files from `fec_crude_csv.py`, I
thought I should write a convenient way to see their contents.  This
program converts such files to JSON.

"""

import sys, cPickle, simplejson

def main(filenames):
    for filename in filenames:
        fo = file(filename)
        while True:
            try:
                record = cPickle.load(fo)
            except EOFError:
                break
            print simplejson.dumps(record, sort_keys=True, indent=4)

if __name__ == '__main__':
    main(sys.argv[1:])
