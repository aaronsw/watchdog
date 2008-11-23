#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This is just some test code right now for exploring the space of
parsing FEC CSV files in a relatively version-flexible way.

As I write this, it takes about 50% more CPU time than the old version
that was chewing through 300 kilobytes per second on my 700MHz
dinosaur --- now it's doing 210 kilobytes per second.

"""
import csv, sys, cgitb, fixed_width, zipfile, StringIO, types

fields_from_fec_csv_py = """
type ('contribution')
for contributions:
    candidate_fec_id
    candidate (first and last name)
    committee
    date
    contributor_org
    contributor
    occupation
    employer
    filer_id
    report_id
    amount
for expenditures:
    candidate
    committee
    date
    recipient
    filer_id
    report_id
    amount
"""

class Field:
    """Represents a field in the output data, and knows how to compute it.

    This is an abstract base class; most concrete subclasses can be
    constructed most conveniently with the factory function
    `as_field`, which creates a sort of tiny DSEL for describing field
    mappings.

    Two of the concrete subclasses can contain Fields themselves;
    CompositeField contains a list of Fields any of which can supply
    its value, and Transform contains a single Field whose value it
    transforms.

    """
    def get_from(self, data):
        "Simple method for testing."
        for key, func in self.inverteds().items():
            if key in data: return func(data)
    def inverteds(self):
        """Return a dictionary of ways to get this field’s value.

        The keys of the dictionary are the names of original source
        fields that must be present for the function to be applicable;
        the values are functions that take the original source data
        dictionary.  Those functions are entitled to access other
        fields in the dictionary, and to throw a KeyError if they want
        to fail.

        This is an efficiency hack; the objective is that we can avoid
        trying to look at fields that aren’t present at all in the
        source data.  It saved only about 14% of user CPU time when I
        tested it.

        """

class InputField(Field):
    """
    >>> f = InputField('bob')
    >>> f.inverteds().keys()
    ['bob']
    >>> f.inverteds()['bob']({'bob': 4, 'mel': 5})
    4
    """
    def __init__(self, name): self.name = name
    def inverteds(self):
        name = self.name
        return {name: lambda data: data[name]}


class Reformat(Field):
    """Changes the format of data in a field.

    >>> Reformat(format=fixed_width.date,
    ...          source=['bob']).get_from({'bob': '20080930'})
    '2008-09-30'
    >>> Reformat(format=fixed_width.date,
    ...          source=['bob']).get_from({'dan': '20080830'})

    Note that the above test failed to return anything.

    >>> f = Reformat(format=lambda x: x, source=['bob', 'fred'])
    >>> sorted(f.inverteds().keys())
    ['bob', 'fred']
    >>> f.inverteds()['bob']({'bob': 39})
    39
    """
    def __init__(self, source, format):
        self._source = as_field(source)
        self._format = format
    def inverteds(self):
        rv = {}
        format = self._format
        for k, v in self._source.inverteds().items():
            # v=v so each lambda has its own v instead of all sharing
            # the same v; it's not intended that callers will override
            # v!
            rv[k] = lambda data, v=v: format(v(data))
        return rv

class MultiInputField(Field):
    """A field whose value is computed from more than one input field.

    Its `inverteds()` includes only one of the input fields, currently
    the shortest one.  That’s because there’s no reason to call it
    repeatedly; if one of the other input fields is missing, it will
    fail harmlessly with a KeyError.

    >>> f = MultiInputField(('a', 'b'), lambda a, b: a + ': ' + b)
    >>> f.inverteds().keys()
    ['a']

    >>> ffunc = f.inverteds().values()[0]
    >>> ffunc({'a': 'foo', 'b': 'bar'})
    'foo: bar'
    """
    def __init__(self, names, function):
        "`names` are the field names from which to get `function`'s args."
        self.names, self.function = names, function
    def inverteds(self):
        names = self.names
        def getter(data):
            return self.function(*[data[k] for k in names])
        return {self.names[0]: getter}

class CompositeField(Field):
    """A field with more than one possible source for its data.

    >>> f = CompositeField(['a', Reformat(source=['b'], format=len)])
    >>> sorted(f.inverteds().keys())
    ['a', 'b']
    >>> f.inverteds()['a']({'a': '90210'})
    '90210'
    >>> f.inverteds()['b']({'b': '90210'})
    5
    """
    def __init__(self, fields):
        self.fields = fields
    def inverteds(self):
        rv = {}
        for field in self.fields: rv.update(as_field(field).inverteds())
        return rv

def argnames(func):
    "Compute a list of the names of the arguments of a Python function."
    return func.func_code.co_varnames[:func.func_code.co_argcount]

def as_field(obj):
    """Coerce obj to some kind of field."""
    if hasattr(obj, 'inverteds'):
        return obj
    elif isinstance(obj, basestring):
        return InputField(obj)
    elif isinstance(obj, types.ListType):
        return CompositeField(obj)
    elif isinstance(obj, types.FunctionType):
        return MultiInputField(argnames(obj), obj)
    raise "can't coerce to a field", obj

class FieldMapper:
    """Maps fields according to a field-mapping specification.

    Takes and returns a dict. The original dict comes out as a
    member named 'original_data'; otherwise its members are only
    copied across according to applicable field specs.

    If the field’s output name is not specifically mentioned among a
    field’s aliases, it isn’t included in the fields to copy from:

    >>> FieldMapper({'a': 'b'}).map({'a': 3})
    {'original_data': {'a': 3}}
    >>> FieldMapper({'a': ['a', 'b']}).map({'a': 3})
    {'a': 3, 'original_data': {'a': 3}}

    >>> mapped = FieldMapper(fields).map({'date_received': '20081131',
    ...                                   'tran_id': '12345', 
    ...                                   'weird_field': 34, 
    ...                                   'amount_received': '123456'})
    >>> sorted(mapped.keys())
    ['amount', 'date', 'original_data', 'tran_id']
    >>> mapped['date']
    '2008-11-31'
    >>> mapped['amount']
    '1234.56'
    >>> mapped['original_data']['weird_field']
    34
    >>> mapped['tran_id']
    '12345'
    """
    def __init__(self, fields):
        self.inverteds = {}
        for name, field in fields.items():
            field = as_field(field)
            self.inverteds.update(dict((k, (name, v))
                                       for k, v in field.inverteds().items()))
        self.inverted_keys = set(self.inverteds.keys())
    def map(self, data):
        rv = {'original_data': data}
        # Here we intersect the keys in the data with the keys we’re
        # interested in, in order to avoid doing unnecessary work in
        # Python.
        for fieldname in set(data.keys()) & self.inverted_keys:
            name, func = self.inverteds[fieldname]
            try:
                v = func(data)
            except KeyError:
                pass
            else:
                rv[name] = v
        return rv

def strip(text):
    """
    >>> strip(' s ')
    's'
    """
    return text.strip()

def amount(text):
    """
    Decode amounts according to `FEC_v300.doc` and its kin.

    >>> map(amount, '50.00 6000 6000.00 600000'.split())
    ['50.00', '60.00', '6000.00', '6000.00']
    """
    if '.' in text: return text
    return text[:-2] + '.' + text[-2:]

fields = {
    'date': Reformat(format=fixed_width.date,
                     source=['date', 'date_received', 'contribution_date']),
    'candidate_fec_id': Reformat(format=strip, source=['candidate_fec_id',
                                                       'candidate_id_number',
                                                       'fec_candidate_id_number']),
    'tran_id': ['tran_id', 'transaction_id_number'],
    'occupation': ['occupation', 'contributor_occupation', 'indocc'],
    'contributor_org': ['contributor_org',
                        'contributor_organization_name',
                        'contrib_organization_name'],
    'employer': ['employer', 'contributor_employer', 'indemp'],
    'amount': Reformat(format=amount,
                       source=['amount',
                               'contribution_amount',
                               'amount_received',
                               'expenditure_amount',
                               'amount_of_expenditure']),
    'address': (lambda street__1, street__2, city, state, zip:
                ' '.join([street__1, street__2, city, state, zip])),
}

fieldmapper = FieldMapper(fields)

def _regrtest_fields():
    """
    Regression tests for the `fields` table.
    
    >>> fieldmapper.map({'candidate_id_number': '12345'})
    ... #doctest: +ELLIPSIS
    {'candidate_fec_id': '12345', 'original_data': {...}}
    >>> fieldmapper.map({'fec_candidate_id_number': '56789'})
    ... #doctest: +ELLIPSIS
    {'candidate_fec_id': '56789', 'original_data': {...}}
    >>> fieldmapper.map({'transaction_id_number': '56789'})
    ... #doctest: +ELLIPSIS
    {'original_data': {...}, 'tran_id': '56789'}
    >>> fieldmapper.map({'contributor_occupation': 'Consultant'})
    ... #doctest: +ELLIPSIS
    {'original_data': {...}, 'occupation': 'Consultant'}
    >>> fieldmapper.map({'indocc': 'Private Investor'})
    ... #doctest: +ELLIPSIS
    {'original_data': {...}, 'occupation': 'Private Investor'}
    >>> fieldmapper.map({'indemp': 'EEA Development'})
    ... #doctest: +ELLIPSIS
    {'original_data': {...}, 'employer': 'EEA Development'}

    >>> fieldmapper.map({'street__1': '2531 Falcon Way',
    ...                  'street__2': '#400',
    ...                  'city': 'Concord',
    ...                  'state': 'TX',
    ...                  'zip': '20036'})
    ... #doctest: +ELLIPSIS
    {...'address': '2531 Falcon Way #400 Concord TX 20036'...}

    """

class header(csv.excel):
    delimiter = ';'
def headers(filename):
    r = csv.reader(file(filename, 'U'), dialect=header)
    rv = {}
    for line in r:
        # some of the format spec files erroneously say SchA rather than SA
        # or erroneously say SH1, SH2, etc., rather than H1, H2, etc.
        key = line[0].replace('Sch', 'S').replace('SH', 'H')
        rv[key] = [name.strip().lower().replace(' ', '_') for name in line[1:]]
    return rv
def findkey(hmap, key):
    """Find the base schedule or form number,
    given the first field from an FEC filing record.
    """
    while key:
        if key in hmap: return hmap[key]
        else: key = key[:-1]

headers_cache = {}
def headers_for_version(version):
    "Memoize headers function, saving about 25–40% of run time."
    if version not in headers_cache:
        headers_cache[version] = \
            headers('../data/crawl/fec/electronic/headers/%s.csv' % version)
    return headers_cache[version]

class ascii28separated(csv.excel):
    delimiter = chr(28)

def readfile(fileobj):
    r = csv.reader(fileobj)
    headerline = r.next()
    if chr(28) in headerline[0]:
        # it must be in the new FS-separated format
        fileobj.seek(0)
        r = csv.reader(fileobj, dialect=ascii28separated)
        headerline = r.next()
    headermap = headers_for_version(headerline[2])
    in_text_field = False
    for line in r:
        if not line: continue         # FILPAC inserts random blank lines
        if line[0].lower() == '[begintext]':
            # see e.g. "New F99 Filing Type for unstructured, formatted text"
            # in FEC_v300.rtf
            in_text_field = True
        if not in_text_field:
            fieldnames = findkey(headermap, line[0])
            if not fieldnames:
                raise "could not find field defs", (line[0], headermap.keys())
            yield fieldmapper.map(dict(zip(fieldnames, line)))
        elif in_text_field:
            # XXX currently discard the contents of text fields
            if line[0].lower() == '[endtext]':
                in_text_field = False

def readfile_zip(filename):
    zf = zipfile.ZipFile(filename)
    for name in zf.namelist():
        for record in readfile(StringIO.StringIO(zf.read(name))):
            yield record

def readfile_generic(filename):
    if filename.endswith('.zip'):
        return readfile_zip(filename)
    else:
        return readfile(file(filename))


if __name__ == '__main__':
    cgitb.enable(format='text')
    for filename in sys.argv[1:]:
        for line in readfile_generic(filename): print line
