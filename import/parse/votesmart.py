import simplejson as json

DATA_DIR='../data'


def items(fname):
    print 'loading', fname
    return json.load(file(DATA_DIR + '/%s.json' % fname)).iteritems()


def candidates():
    return items('crawl/votesmart/candidates')


def bios():
    return items('crawl/votesmart/bios')


def websites():
    return items('crawl/votesmart/websites')


def districts():
    return items('crawl/votesmart/districts')
