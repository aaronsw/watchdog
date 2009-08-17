import web
import webapp
import petition
import inspect, types, itertools, gzip, os
from web.browser import AppBrowser

single_pages = ('/', '/about', '/about/team', '/about/api', '/about/feedback', '/about/help',
                '/contribute/', '/blog/',
                '/lob/c/', '/lob/f/', '/lob/o/', '/lob/pa/', '/lob/pe/',
                '/b/', '/e/', '/p/', '/c/', '/writerep/')

b = AppBrowser(webapp.app)

def test(klass):
    index = klass().index()
    for path in do_flatten(take(2, iter(index))):
        try:
            b.open(path)
            assert(b.status == 200)
        except:
            print b.status, path, klass

def get_class_index(klass, _test=False):
    try:
        if _test:
            return test(klass)  
        return klass().index()
    except AttributeError:
        return []

def do_flatten(d):
    """
    >>> list(do_flatten([1, 2, 3]))
    [1, 2, 3]
    >>> list(do_flatten([1, [2, [3]], [4, [5]]]))
    [1, 2, 3, 4, 5]
    """
    for x in d:
        if type(x) in [types.ListType, types.GeneratorType, types.TupleType]:
            for y in do_flatten(x):
                yield y
        else:
            yield x

def flatten(f):
    def g(*args, **kw):
        return do_flatten(f(*args, **kw))
    return g

@flatten
def getindex(app, _test=False):
    for page in single_pages:
        yield page
    kns = list(app.fvars['urls'])[1::2]
    for kn in kns:
        if isinstance(kn, types.StringType):
            if '.' in kn:
                modname, kls = kn.split('.')
                mod = __import__(modname)
                kls = getattr(mod, kls, None)
            else:    
                kls = app.fvars[kn]
            yield get_class_index(kls, _test)
        elif isinstance(kn, web.application):
            yield getindex(kn, _test)

def take(n, seq):
    for i in xrange(n):
        yield seq.next()

def group(seq, maxsize):
    def limit(seq, maxsize, itemlen):
        size = 0
        while size < maxsize:
            x = seq.next()
            if not x: break
            size += itemlen(x)
            yield x
    
    overhead = len('<a href=""></a>\n')
    itemlen = lambda x: overhead+2*len(x)
    x = 1
    while x:
        x = list(limit(seq, maxsize, itemlen))
        yield x

t_sitemap = """$def with (title, items)
<style>a{display:block;}</style>
<h1>Index</h1>
<a href="index.html">Back</a> | <a href="../index.html">Back to index</a></br>
$for item in items:
    <a href="$item">$item</a>
<a href="index.html">Back</a> | <a href="../index.html">Back to index</a>
"""

t_index = """$def with (title, items)
<style>a{display:block;}</style>
<h1>$title</h1>

$if title != "index": <a href="../index.html">Back to index</a>
$for item in items:
    <a href="$item">$item</a>
$if title != "index": <a href="../index.html">Back to index</a>
"""

make_sitemap = web.template.Template(t_sitemap)
make_index = web.template.Template(t_index)
pagesize = 99*1024 #1K for overheads like <h1> and back links
entries_per_page = pagesize/50  #len('<a href="index_xxxxx.html">index_xxxxx.html</a>') = 47

def write(filename, text):
    f = open(filename, 'w')
    f.write(text)
    print filename, len(text)/1024
    f.close()

def write_sitemap(i, seq, index_dir):
    dir = index_dir + '/%02d' % (i/entries_per_page)
    filename = "%s/index_%05d.html" % (dir, i)
    if not os.path.exists(dir):
        os.mkdir(dir)
    write(filename, str(make_sitemap(filename, seq)))

def write_sitemaps(data, index_dir, offset=0):
    for i, x in enumerate(group(data, pagesize)):
        write_sitemap(i+offset, x, index_dir)

def create_index(index_dir, _test=False):
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    
    data = getindex(webapp.app, _test)
    write_sitemaps(data, index_dir)
    
    dirs = [d for d in os.listdir(index_dir) if os.path.isdir(os.path.join(index_dir, d))]
    write(index_dir + '/index.html', str(make_index(index_dir, [d+'/index.html' for d in dirs])))

    for d in dirs:
        d = os.path.join(index_dir, d)
        write(d + '/index.html', str(make_index('index %s' % (d), os.listdir(d))))
    
if __name__ == "__main__":
    create_index('static/index', _test=False)
