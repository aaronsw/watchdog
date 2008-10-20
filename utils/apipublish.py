"""
publish Python objects as various API formats
"""

import datetime
import simplejson as json
import web

API_PREFIX = "http://watchdog.net/about/api#"

def _listify(v):
    if v is None:
        return []
    elif not isinstance(v, list):
        return [v]
    else:
        return v

def _getitems(obj, listify=True):
    out = []
    for k in obj.columns:
        c = obj.columns[k]
        if hasattr(c, 'export') and not c.export:
            pass
        else:
            v = getattr(obj, k)
            if listify: v = _listify(v)
            out.append((k, c, v))
    out.sort(lambda x, y: cmp(x[0], y[0]))
    return out

class SmartJSONEncoder(json.JSONEncoder):
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
            try:
                return super(SmartJSONEncoder, self).default(obj)
            except TypeError:
                try:
                    return json.dumps(obj)
                except:
                    try:
                        return obj._uri_
                    except:
                        return None
    
    def default(self, obj):
        return getattr(obj, 'tojson', lambda: self._default(obj))()

def tojson(x):
    return json.dumps(x, cls=SmartJSONEncoder)

def publishjson(lst):
    out = ['[']
    for obj in lst:
        out.append('  {')
        out.append('    "_type": "%s",' % obj.__class__.__name__)
        out.append('    "uri": "%s",' % obj._uri_)
        for k, c, v in _getitems(obj, listify=False):
            out.append('    "%s": %s,' % (k, tojson(v)))
        out[-1] = out[-1][:-1]
        out.append('  }')
    out.append(']\n')
    return '\n'.join(out)

n3_basic_indent = '  '

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
        return '"%s"' % unicode(obj).replace('"', r'\"')

def n3ify(obj, indent, c=None):
    if hasattr(obj, 'ton3'):
        return obj.ton3(indent)
    elif hasattr(c, 'ton3'):
        return c.ton3(obj, indent)
    else:
        return _n3ify(obj, indent)

def publishn3(lst):
    indent = n3_basic_indent
    out = ['@prefix : <%s> .' % API_PREFIX, '']
    for obj in lst:
        out.append('<%s> a :%s;' % (obj._uri_, obj.__class__.__name__))
        for k, c, v in _getitems(obj):
            for item in v:
                n3v = n3ify(item, indent, c)
                if not n3v: continue
                out.append(indent + 
                  ':%s %s;' % (k, n3v)
                )
        if hasattr(obj, 'n3lines'): out.extend(obj.n3lines(indent))
        out.append('.\n')
    return '\n'.join(out)

def publishxml(lst):
    out = [
      '<?xml version="1.0"?>',
      '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"',
      '  xmlns="%s"' % API_PREFIX,
      '  xmlns:x="%s">' % API_PREFIX]
    for obj in lst:
        objtype = obj.__class__.__name__
        out.append('<%s rdf:about="%s">' % (objtype, obj._uri_))
                
        for k, c, v in _getitems(obj):
            for item in v:
                xmlv = c.toxml(item)
                if not xmlv: continue
                outline = '  <%s%s</%s>' % (k, xmlv, k)
                outline = outline.replace('></%s>' % k, ' />') # clean up empty values
                out.append(outline)
        if hasattr(obj, 'xmllines'): out.extend(obj.xmllines())
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

def publish(lst, ftype=None):
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
