#!/usr/bin/python
# Read Aaron's crawl of the votesmart.org API data.
import sets, pickle

def summary(fo):
    keys = sets.Set()
    other = sets.Set()
    for x in pickle.load(fo):
        if hasattr(x, 'keys'):
            keys |= sets.Set(x.keys())
        else:
            other.add(x)
    return '%s %s' % (keys, other)
def main():
    for fname in 'districts candidates officials'.split():
        print summary(file(fname + '.pkl'))
if __name__ == '__main__': main()
