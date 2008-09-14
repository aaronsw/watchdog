## Types used in definitions

def date(s):
    return s[0:4] + '-' + s[4:6] + '-' + s[6:8]

def year(s):
    return '20' + s

def string(s):
    return s.strip()

def boolean(s):
    return {'Y': True, 'N': False, ' ': None}[s]
    
filler = string

def enum(s=None, **db):
    if isinstance(s, basestring):
        return string(s)
    else:
        if ' ' not in db: db[' '] = None
        return lambda s: db[s]

def table_lookup(table, preProcess=None):
    def get_from_table(d):
        if preProcess:
            d=preProcess(d)
        if d in table:
            return table[d]
        else:
            return string(d)
    return get_from_table

def integer(s):
    s = s.strip()
    if s:
        try:
            return int(s)
        except ValueError:
            return s
    else: return None

## Format of the definitions

FIELD_KEY = 0
FIELD_LEN = 1
FIELD_TYP = 2


## The functions you might want to call

def parse_line(linedef, line):
    assert(line[-1] in '\n\r')
    out = {}
    n = 0
    for (k, l, t) in linedef:
        if k is not None:
            out[k] = t(line[n:n+l])
        n += l
    return out

def get_len(filedef):
    linelen = set(sum(line[FIELD_LEN] for line in kind) for kind in filedef.itervalues())
    assert len(linelen) == 1, [(kind_name, sum(line[FIELD_LEN] for line in kind)) for kind_name, kind in filedef.iteritems()]
    linelen = list(linelen)[0]
    return linelen

def parse_file(filedef, fh, f_whichdef=None):
    linelen = get_len(filedef)
    if not f_whichdef: f_whichdef = lambda x: x[0]
    for line in iter(lambda: fh.read(linelen), ''):
        yield parse_line(filedef[f_whichdef(line)], line)

