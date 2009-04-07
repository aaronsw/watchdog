import web
import webapp
import petition
import inspect, types, itertools, gzip, os

single_pages = ('/', '/about', '/about/team', '/about/api', '/about/feedback', '/about/help',
                '/contribute/', '/blog/',
                '/lob/c/', '/lob/f/', '/lob/o/', '/lob/pa/', '/lob/pe/',
                '/b/', '/e/', '/p/', '/c/', '/writerep/')

def get_class_index(klass, _test=False):
    try:
        if _test:
            print klass
            return take(5, iter(klass().index()))
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

def group(seq, n):
    while True:
        x = list(take(n, seq))
        if x: 
            yield x
        else:
            break        

t_sitemap = """$def with (title, items)
<h1>Index</h1>
<a href="index.html">Back</a> | <a href="../index.html">Back to index</a></br>
$for item in items:
    <a href="$item">$item</a>
<a href="index.html">Back</a> | <a href="../index.html">Back to index</a>
"""

t_index = """$def with (title, items)
<h1>$title</h1>

$if title != "index": <a href="../index.html">Back to index</a>
$for item in items:
    <a href="$item">$item</a>
$if title != "index": <a href="../index.html">Back to index</a>
"""

make_sitemap = web.template.Template(t_sitemap)
make_index = web.template.Template(t_index)
entries_per_page = 2200

def write(filename, text):
    f = open(filename, 'w')
    f.write(text)
    f.close()

def write_sitemap(i, seq):
    dir = 'index/%02d' % (i/entries_per_page)
    filename = "%s/index_%05d.html" % (dir, i)
    if not os.path.exists(dir):
        os.mkdir(dir)
    write(filename, str(make_sitemap(filename, seq)))
    print filename

def write_sitemaps(data):
    for i, x in enumerate(group(data, entries_per_page)):
        write_sitemap(i, x)

def create_index(index_dir, _test=False):
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)

    data = getindex(webapp.app, _test)
    write_sitemaps(data)

    dirs = [d for d in os.listdir('index') if os.path.isdir(os.path.join('index', d))]
    write('index/index.html', str(make_index('index', [d+'/index.html' for d in dirs])))

    for d in dirs:
        d = os.path.join('index', d)
        write(d + '/index.html', str(make_index('index %s' % (d), os.listdir(d))))
    
if __name__ == "__main__":
    create_index('index', _test=False)
