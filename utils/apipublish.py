"""
publish Python objects as various API formats
"""

import datetime
import simplejson
import web

## Basic data transformation

def transform_item(fields, datum):
    "Transform a dict for publication using a dict of field definitions."
    rv = {}
    for k, v in fields.items():
        for k in k.split():
            if callable(v): rv[k] = v(datum[k])
            elif hasattr(v, 'generic'): rv[k] = v.generic(datum)
            else: rv[k] = v
    return rv

def transform_table(fields, data):
    "Transform a list of dicts for publication with `transform_item`."
    return [transform_item(fields, datum) for datum in data]

## Field types

class URI:
    def __init__(self, uri): self.uri = uri
    def n3ify(self, indent): return '<%s>' % self.uri
    def jsonify(self): return self.uri

identity = lambda x: x

class generic:
    "Generic publishable data field computed from the whole source object."
    def __init__(self, thunk): self.thunk = thunk
    def generic(self, obj): return self.thunk(obj)

class table:
    def __init__(self, fields): self.fields = fields
    def __call__(self, data): return transform_table(self.fields, data)

##

exampleobj = [
  {
    'uri': 'http://watchdog.net/us/ca-12',
    'type': 'District',
    'name': 'CA-12',
    'state': 'CA',
    'district': 12,
    'voting': True,
    'wikipedia': URI("http://en.wikipedia.org/wiki/California's_12th_congressional_district"),
    'population': None
  }
]

class SmartJSONEncoder(simplejson.JSONEncoder):
    #@@ I got rid of the date field in schema.sql.  I think that means
    # that we can dump all this isinstance date handling stuff?
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"
    def _default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%sT%sZ" % (self.DATE_FORMAT, self.TIME_FORMAT))
        elif isinstance(obj, datetime.date):
            return obj.strftime(self.DATE_FORMAT)
        elif isinstance(obj, datetime.time):
            return obj.strftime(self.TIME_FORMAT)
        else:
            return super(SmartJSONEncoder, self).default(obj)
    def default(self, obj):
        return getattr(obj, 'jsonify', lambda: self._default(obj))()

def publishjson(obj):
    return simplejson.dumps(
        obj, indent=2, sort_keys=True, cls=SmartJSONEncoder) + '\n'

n3_basic_indent = '  '

def n3ify_dict(obj, indent):
    return '[\n%s\n%s]' % (n3ify_items(obj, indent + n3_basic_indent), indent)

def _n3ify(obj, indent):
    if isinstance(obj, dict):
        return n3ify_dict(obj, indent)
    elif isinstance(obj, list):
        return ', '.join([n3ify(item, indent + n3_basic_indent)
                          for item in obj])
    elif isinstance(obj, bool):
        return str(obj).lower()
    elif isinstance(obj, (int, float)):
        return obj
    else:
        return '"%s"' % str(obj).replace('"', r'\"')

def n3ify(obj, indent):
    return getattr(obj, 'n3ify', lambda indent: _n3ify(obj, indent))(indent)

def n3ify_items(obj, indent):
    objitems = obj.items()
    objitems.sort(lambda x, y: cmp(x[0], y[0]))
    return '\n'.join(['%s:%s %s;' % (indent, k, n3ify(v, indent))
                      for k, v in objitems if v is not None])

def publishn3(lst, pkey='id'):
    out = ['@prefix : <http://watchdog.net/about/api#> .', '']
    for obj in lst:
        obj = obj.copy()
        out.append('<%s> a :%s;' % (obj.pop('uri'), obj.pop('type')))
        out.append(n3ify_items(obj, indent=n3_basic_indent))
        out.append('.\n')
    return '\n'.join(out)

def xmlify(obj):
    if isinstance(obj, dict):
        # must be only strings as values and words as keys
        return ' %s>' % ' '.join('x:%s="%s"' % (web.websafe(k), web.websafe(v))
                                 for k, v in obj.items())
    elif isinstance(obj, bool):
        return ' rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">%s' % web.websafe(obj).lower()
    elif isinstance(obj, int):
        return ' rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">%s' % web.websafe(obj)
    elif isinstance(obj, float):
        return ' rdf:datatype="http://www.w3.org/2001/XMLSchema#double">%s' % web.websafe(obj)
    elif isinstance(obj, URI):
        return ' rdf:resource="%s">' % web.websafe(obj.uri)
    else:
        return '>' + web.websafe(obj)

def publishxml(lst):
    out = [
      '<?xml version="1.0"?>',
      '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"',
      '  xmlns="http://watchdog.net/about/api#"',
      '  xmlns:x="http://watchdog.net/about/api#">']
    for obj in lst:
        obj = obj.copy()
        objtype = obj.pop('type')
        out.append('<%s rdf:about="%s">' % (objtype, obj.pop('uri')))
        objitems = obj.items()
        objitems.sort(lambda x, y: cmp(x[0], y[0]))
        for k, v in objitems:
            if v is None: v = []
            if not isinstance(v, list): v = [v]
            for item in v:
                outline = '  <%s%s</%s>' % (k, xmlify(item), k)
                outline = outline.replace('></%s>' % k, ' />') # clean up empty values
                out.append(outline)
        out.append('</%s>' % objtype)
    out.append('</rdf:RDF>')
    return '\n'.join(out) + '\n'

def _findq(x):
    """
    Find the associated quality level with a media type instance:
    
        >>> _findq('text/xml')
        (1, 'text/xml')
        >>> _findq('text/xml;level=1')
        (1, 'text/xml')
        >>> _findq('text/xml;level=1;q=.5')
        (0.5, 'text/xml')
        >>> _findq('text/xml; level=2; q=.5')
        (0.5, 'text/xml')
        >>> _findq('text/xml;q=.5;level=1')
        (0.5, 'text/xml')
    """
    options = x.split(';')
    mediatype = options[0].strip()
    for option in options[1:]:
        option = option.strip()
        if option.startswith('q='):
            q = float(option[2:])
            break
    else:
        q = 1
    return (q, mediatype)

def bestaccepted(options, source=None):
    """
    @@move to web.py
    
    Find the media type in `options` that best matches the 
    acceptable options in `source` (or the `Accept:` header if
    `source` is None).
    
        >>> bestaccepted(
        ...  ['application/xml+xhtml', 'text/html', 'text/plain'], 
        ...  'text/plain; q=0.5, text/html, text/x-dvi; q=0.8, text/x-c')
        'text/html'
        >>> bestaccepted(
        ...  ['application/pdf', 'text/html'],
        ...  'text/*;q=.4, application/pdf;q=.2')
        'text/html'
        >>> bestaccepted(
        ...  ['application/pdf', 'text/html'],
        ...  '*/*;q=1, text/html; q=.2')
        'application/pdf'
    
    todo: support quality factors on input
    todo: send a 406 if no match
    """
    if source is None:
        source = web.ctx.env.get('HTTP_ACCEPT', '')
    
    accepts = [_findq(x) for x in source.split(',')]
    accepts.sort(reverse=True)
    for q, mtype in accepts:
        if mtype in options:
            return mtype
        elif mtype == '*/*':
            return options[0]
        elif mtype.endswith('/*'):
            for option in options:
                if option.startswith(mtype[:-1]):
                    return option
    return options[0] #@@ should probably send a 406

def publish(fields, rawdata, ftype=None):
    lst = transform_table(fields, rawdata)
    preferences = ['html', 'n3', 'json', 'xml']
    ftype_map = {
      'html': 'text/html',
      'n3': 'text/rdf+n3',
      'json': 'application/json',
      'xml': 'application/rdf+xml'
    }
    if ftype:
        format = ftype_map[ftype]
    else:
        format = bestaccepted([ftype_map[x] for x in preferences])
    if format == 'text/html':
        return False
    elif format == 'text/rdf+n3':
        web.header('Content-Type', 'text/rdf+n3')
        return publishn3(lst)
    elif format == 'application/rdf+xml':
        web.header('Content-Type', 'application/rdf+xml')
        return publishxml(lst)
    elif format == 'application/json':
        web.header('Content-Type', 'application/json')
        return publishjson(lst)
    else:
        raise ValueError, 'unknown format'

if __name__ == "__main__":
    print publishjson(exampleobj)
    print
    print publishn3(exampleobj)
    print
    print publishxml(exampleobj)
