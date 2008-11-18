"""
smartersql: A smarter interface to SQL.
"""
import web

## lazy loading

def lazylookup(obj, column_name):
    def inner(obj2):
        # obj is obj2
        
        # If we're being called, that means someone's trying to access
        # a lazy reference on obj.

        column = obj.columns[column_name]
        objs = obj._objs

        # First, we need to get the answer for all of us:
        if isinstance(column, Backreference):
            column.target = column._target()
            local_column = column.local_column.sql_name
            target_column = column.target_column
            order = column.order
            plural = column.plural

        else:
            local_column = column.sql_name
            target_column = column.target_column.sql_name
            order = None
            plural = False
            
        newobjs = {}
        for k in column.target.select(
          order=order,
          where=web.sqlors(target_column + ' = ', 
          [getattr(x, local_column) for x in objs])):
            val = getattr(k, target_column)
            if plural:
                newobjs.setdefault(val, []).append(k)
            else:
                newobjs[val] = k
    
        # Then we need to add it to all of us:
        for xobj in objs:
            k = getattr(xobj, local_column)
            if k in newobjs:
                setattr(xobj.__class__, column_name, newobjs[k])
    
        # Finally, we need to return it:
        return newobjs.get(getattr(obj, local_column))
    return inner
    
## table generation

_all_tables = []

class metatracker(type):
    def __init__(self, name, bases, *a, **kw):
        type.__init__(self, name, bases, *a, **kw)
        if bases[0] != object and not hasattr(self, 'columns'):
            _all_tables.append(self)
            self.columns = self._analyze(init=True)
            self.primary = self._primary(self.columns)
            self.sql_name = self._sql_name_()
            

class Table(object):
    __metaclass__ = metatracker

    @classmethod
    def _sql_name_(cls):
        return cls.__name__.lower()
    
    @classmethod
    def _analyze(cls, init=False):
        columns = web.Storage()
        
        for k in dir(cls):
            if isinstance(getattr(cls, k), Column):
                v = getattr(cls, k)
                v.sql_name = v._sql_name_(k)
                if not hasattr(v, 'label'):
                    v.label = k.replace('_', ' ')
                if init and hasattr(v, '_delayed_init'):
                    v._delayed_init(cls)
                columns[k] = v
        return columns
    
    @staticmethod
    def _primary(columns):
        primary = web.Storage()
        for k, v in columns.iteritems():
            if v.primary:
                primary[k] = v
        return primary
    
    @classmethod
    def _createSQL(cls):        
        x = 'CREATE TABLE %s (\n' % cls.sql_name
        for k, v in cls.columns.iteritems():
            if not v.sql_type: continue # not for sql
            
            x += '  %s %s' % (v.sql_name, v.sql_type)
            if v.unique: x += ' UNIQUE'
            if v.notnull: x += ' NOT NULL'
            if v.default: x += ' DEFAULT %s' % x.default
            x += ',\n'
        if cls.primary:
            x += '  PRIMARY KEY (%s)\n' % ', '.join(v.sql_name for v in cls.primary.itervalues())
        else:
            x = x[:-2] + '\n' # remove last comma
            
        x += ')'
        return x
    
    @classmethod
    def _dropSQL(cls, cascade=False):
        cascade = " CASCADE" if cascade else ""
        return 'DROP TABLE IF EXISTS %s%s' % (cls.sql_name, cascade)
    
    @classmethod
    def create(cls): cls.db.query(cls._createSQL())
    @classmethod
    def drop(cls, cascade=False): cls.db.query(cls._dropSQL(cascade))
    @classmethod
    def insert(cls, *a, **kw):
        #@@ deal with seqname
        #@@ convert objects to the proper identifiers
        cls.db.insert(cls.sql_name, *a, **kw)
    @classmethod
    def select(cls, what='*', **kw):
        rows = cls.db.select(cls.sql_name, what=what, **kw)
        objs = [cls(x) for x in rows]
        for o in objs:
            #@@ make weakref?
            o._objs = objs # so lazy references can fill in their neighbors
        return objs
        
    @classmethod
    def where(cls, **clauses):
        out = ""
        for k, v in clauses.items():
            out += k + '=' + web.sqlquote(v)
        
        return cls.select(where=out)
    
    def __init__(self, row, ids=None):
        if ids: self._ids = ids
        
        # divorce ourself from the parent class, so we can edit it
        c = self.__class__
        self.__class__ = type(c.__name__, c.__bases__, dict(c.__dict__))
        
        for k, v in self.columns.iteritems():
            if isinstance(v, Reference):
                setattr(self.__class__, k, property(lazylookup(self, k)))
            
            if v.sql_type:
                setattr(self, v.sql_name, row[v.sql_name])


## columns

class Column(object):
    def __init__(self, **kw):
        for k in kw:
            setattr(self, k, kw[k])
    
    _sql_name_ = lambda self, k: k

    default = None
    primary = False
    unique = False
    notnull = False

    display = lambda self, x: unicode(x)
    toxml = lambda self, obj: '>' + web.htmlquote(unicode(obj))

class Reference (Column):
    def __init__(self, target, **kw):
        super(Reference, self).__init__(**kw)
        assert len(target.primary) == 1, \
          "Referenced column must have exactly 1 primary key."

        self.target = target
        self.target_column = target.primary.values()[0]
        
        self.sql_type = self.target_column.sql_type + ' REFERENCES ' + target.sql_name
        self._sql_name_ = lambda k: k + '_id'
    
    def toxml(self, obj):
        if hasattr(obj, '_uri_'):
            return ' rdf:resource="%s">' % web.websafe(obj._uri_)
        else:
            return None
    def ton3(self, obj, indent):
        if hasattr(obj, '_uri_'):
            return '<%s>' % obj._uri_
        else:
            return None

class Backreference (Reference):
    def __init__(self, target, target_column, plural=True, order=None):
        self._targetk = target
        self.target_column = target_column + '_id'
        self.plural = plural
        self.order = order
        self.sql_type = None
    
    def _delayed_init(self, cls):
        primary = cls._primary(cls._analyze())
        assert len(primary) == 1, \
          "Backreferences with composite primary keys isn't supported."
        self.local_column = primary.values()[0]
    
    def _target(self):
        return [x for x in _all_tables if x.__name__ == self._targetk][0]
    
        
class String (Column):
    sql_type = 'text'
    def __init__(self, length=None, **kw):
        super(String, self).__init__(**kw)
        if length:
            self.sql_type = 'varchar(%s)' % length

class Boolean(Column):
    sql_type = 'bool'
    display = lambda self, x: {True: 'Yes', False: 'No', None: 'Unknown'}
    toxml = lambda self, obj: ' rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">%s' % web.websafe(obj).lower()

class Integer(Column):
    sql_type = 'int'
    toxml = lambda self, obj: ' rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">%s' % web.websafe(obj)
    
class Float(Column):
    sql_type = 'real'
    toxml = lambda self, obj: ' rdf:datatype="http://www.w3.org/2001/XMLSchema#double">%s' % web.websafe(obj)
    

class Serial(Integer): sql_type = 'serial'
class Int2(Integer): sql_type = 'int2'
class Date(Column): sql_type = 'date'

class Year(Integer): pass

class Number(Integer):
    display = lambda self, x: web.commify(x)

class Dollars(Integer):
    display = lambda self, x: '$' + web.commify(x)

class Percentage(Float):
    precision = 3
    display = lambda self, x: str(x*100)[:self.precision + 1] + '%' 
    # add one for the decimal point

class URL(String):
    toxml = lambda self, obj: ' rdf:resource="%s">' % web.websafe(obj)
    ton3 = lambda self, obj, indent: '<%s>' % obj

## module functions

def create():
    for table in _all_tables:
        table.create()

def drop():
    x = list(_all_tables)
    x.reverse()
    for table in x:
        table.drop(cascade=True)

def recreate():
    drop()
    create()

def grantall(username):
    for table in _all_tables:
        try:
            table.db.query('GRANT ALL ON %s TO %s' % (table.sql_name, username))
        except:
            pass
