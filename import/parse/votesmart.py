import simplejson as json

DATA_DIR='../data/crawl/votesmart/111'

def items(fname):
    print 'loading', fname
    return json.load(file(DATA_DIR + '/%s.json' % fname)).iteritems()

def candidates():
    return items('candidates')

def bios():
    return items('bios')

def websites():
    return items('websites')

def districts():
    return items('districts')
