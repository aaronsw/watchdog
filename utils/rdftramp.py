"""rdftramp: Makes RDF look like Python data structures."""
__version__ = 1.1
__copyright__ = "(C) 2008 Aaron Swartz <http://www.aaronsw.com/>. GNU GPL 3."

"""
2008-04-24: 1.1. rename rdftramp, add support for ints and floats
2002-11-17: 1.0. first release
"""

from rdflib import URIRef as URI, Literal
from rdflib.Graph import Graph

class Namespace:
        """A class so namespaced URIs can be abbreviated (like dc.subject).
        label provides the abbreviation that should be used on output)"""

        def __init__(self, prefix, label=''): 
                self.prefix = prefix; self.label = label
        def __getattr__(self, name): return URI(self.prefix + name)
        def __getitem__(self, name): return URI(self.prefix + name)
        
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'rdf')
rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#', 'rdfs')
xsd = Namespace('http://www.w3.org/2001/XMLSchema#', 'xsd')
rss = Namespace('http://purl.org/rss/1.0/', 'rss')
daml = Namespace('http://www.daml.org/2001/03/daml+oil#', 'daml')
log = Namespace('http://www.w3.org/2000/10/swap/log#', 'log')
dc = Namespace('http://purl.org/dc/elements/1.1/', 'dc')
foaf = Namespace('http://xmlns.com/foaf/0.1/', 'foaf')
doc = Namespace('http://www.w3.org/2000/10/swap/pim/doc#', 'doc')
cc = Namespace('http://web.resource.org/cc/', 'cc')
content = Namespace('http://purl.org/rss/1.0/modules/content/', 'content')

class Thing:
    """Takes an RDF object and makes it look like a dictionary."""
    def __init__(self, name, store): self.name, self.store = name, store
    
    def __getitem__(self, v):
        out = list(self.store.objects(self.name, v))
        out = [thing(x, self, v) for x in out]
        
        if len(out) == 1:
            return out[0]
        else:
            return PsuedoList(out, self, v)
    
    def __setitem__(self, k, v):
        if isinstance(v, Thing): v = v.name
        for triple in self.store.triples((self.name, k, None)):
            self.store.remove((triple[0], triple[1], triple[2]))
                    
        if not isinstance(v, list): v = [v]
        for val in v:
            if not isinstance(val, URI) and isinstance(val, (unicode, str, int, float)):
                val = Literal(val)
            self.store.add((self.name, k, val))
    
    def __iter__(self):
        #@@ add support for new-style lists?
        i = 1
        while rdf["_" + `i`] in self: 
            yield self[rdf["_" + `i`]]
            i += 1

    def __contains__(self, val): return not not self[val]

    def __repr__(self): return repr(self.name)
    def __str__(self): return str(self.name)

    def __eq__(self, other): 
        if isinstance(other, Thing): return self.name == other.name
        else: return self.name == other

def thing(x, store, prop):
    if isinstance(x, URI): return Thing(x, store.store)
    if isinstance(x, (Thing, PsuedoBase)): return x
    if isinstance(x, Literal):
        if x.datatype in [xsd.integer, xsd.int]:
            return PsuedoInteger(x, store, prop)
        elif x.datatype == xsd.float:
            return PsuedoFloat(x, store, prop)
        else:
            return PsuedoString(x, store, prop)
    raise ValueError, "couldn't thingify %s (a %s)" % (x, x.__class__)

class PsuedoBase(object):        
    def __new__(self, name, thing, item):
        self = super(PsuedoBase, self).__new__(self, name)
        self._thing, self._item = thing, item
        return self

    def append(self, x):
        self._thing[self._item] = [self, x]

class PsuedoString(PsuedoBase, unicode): pass
class PsuedoInteger(PsuedoBase, int): pass
class PsuedoFloat(PsuedoBase, float): pass
class PsuedoList(PsuedoBase, list):
    def __init__(self, name, thing, item):
        list.__init__(self, name)
        self._thing, self._item = thing, item
    
    def append(self, x):
        self._thing[self._item] = list(self) + [x]



if __name__ == "__main__":
    # Unit tests, baby!
    
    store = Graph(); ex = Namespace("http://example.org/")
    Aaron = Thing(URI("http://me.aaronsw.com/"), store)
    Aaron == Thing(URI("http://me.aaronsw.com/"), store)
    
    Aaron[ex.name] = "Aaron Swartz"
    assert Aaron[ex.name] == "Aaron Swartz"
    Aaron[ex.homepage] = URI("http://www.aaronsw.com/")
    assert Aaron[ex.homepage] == URI("http://www.aaronsw.com/")
    
    Aaron[ex.machine] = ["vorpal", "slithy"]
    assert Aaron[ex.machine].sort() == ["vorpal", "slithy"].sort()
    # (we sort because order isn't necessarily preserved)
    Aaron[ex.machine] = ["vorpal"]
    # (this replaces old triples)
    assert Aaron[ex.machine] == "vorpal"
    # (if there's only one, it's returned as itself)
    Aaron[ex.machine].append("slithy")
    # (this adds a triple)
    assert Aaron[ex.machine].sort() == ["vorpal", "slithy"].sort()
    Aaron[ex.machine].append('tumtum')
    assert Aaron[ex.machine].sort() == ["vorpal", "slithy", "tumtum"].sort()
    
    # let's do numbers!
    Aaron[ex.age] = 14
    assert Aaron[ex.age] == 14
    Aaron[ex.age] = 14.1
    assert Aaron[ex.age] == 14.1
    
    
    # Lists are hard to make because you shouldn't be making them
    r = rdf
    f = Aaron[ex.topFiveFrobs] = Thing(ex.frobList9028292, store)
    f[r.type] = r.Seq
    f[r._1], f[r._2], f[r._3], f[r._4], f[r._5] = \
        "John", "Jacob", "Jingle", "Heimer", "Schmidt"
    # but since other people did, we still parse them
    n = 0; frobs = ["John", "Jacob", "Jingle", "Heimer", "Schmidt"]
    for frob in Aaron[ex.topFiveFrobs]:
        assert frob == frobs[n]
        n += 1
    assert n == 5
    
    # "pred in subj" == bool(subj[pred])
    assert ex.children not in Aaron
    # you probably don't need it since subj[pred] returns [], not error
    assert not Aaron[ex.children]

    assert str(Aaron) == "http://me.aaronsw.com/"
    assert str(Aaron[ex.name]) == "Aaron Swartz"
    
# Mark Nottingham's Sparta <http://www.mnot.net/sw/sparta/> inspired TRAMP.
# I am open to an LGPL license if you have a convincing reason.
