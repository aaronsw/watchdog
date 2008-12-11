#!/usr/bin/python
# -*- coding: utf-8; -*-
"""Field mapping
================

When you have a big pile of dicts in slightly different formats, and
you want to transform them to dicts in a consistent format, this
module lets you write the field mappings in a small amount of code and
execute them reasonably quickly.

Quick start
-----------

    >>> m = FieldMapper({'age': ['Age', 'age'], 'lastname': 'sname'})
    >>> [m.map(x) for x in [dict(Age=30, sname='Smith'),
    ...                     dict(age=49, sname='Wilson'),
    ...                     dict(x=3, y=4, lastname='Jones')]]
    ... #doctest: +NORMALIZE_WHITESPACE
    [{'lastname': 'Smith', 'age': 30,
      'original_data': {'Age': 30, 'sname': 'Smith'}},
     {'lastname': 'Wilson', 'age': 49,
      'original_data': {'age': 49, 'sname': 'Wilson'}},
     {'original_data': {'y': 4, 'lastname': 'Jones', 'x': 3}}]

You can include functions as mappings; it looks for their argument
names in the input data.

    >>> m = FieldMapper({'age': ['age', lambda birthyear: 2008 - birthyear]})
    >>> m.map({'age': 27})
    {'age': 27, 'original_data': {'age': 27}}
    >>> m.map({'birthyear': 1970})
    {'age': 38, 'original_data': {'birthyear': 1970}}
    >>> m = FieldMapper({'date': lambda year, month, day:
    ...                          '%s-%s-%s' % (year, month, day)})
    >>> m.map(dict(year=2008, month=11, day=19))['date']
    '2008-11-19'

You can construct (slightly) more complicated pipelines with `Reformat`:

    >>> def invert_name(n):
    ...     last, first = n.split(',')
    ...     return '%s %s' % (first.strip(), last.strip())
    >>> m = FieldMapper({'name': Reformat(format=invert_name,
    ...                                   source=['name', 'fullname'])})
    >>> m.map({'name': 'Smith, John'})['name']
    'John Smith'
    >>> m.map({'fullname': 'Smith,John'})['name']
    'John Smith'

Finally, you can use `CatchAllField` (q.v.) to handle cases where these
tools don’t cut it.

BUGS
----

-  Any particular input field can be used reliably by at most one
   output field.  If you try to use the same input field for more than
   one thing, you may get an `AssertionError`.  (You can often work
   around this with `CatchAllField` — just set its `inputs` to
   non-conflicting input field names.)

        >>> FieldMapper({'name': lambda firstname, lastname: firstname + ' ' + lastname,
        ...              'firstname': 'firstname', 'lastname': 'lastname'})
        ... #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        AssertionError: ...

- You can’t construct *arbitrarily* more complicated pipelines with
  `Reformat`.
- It’s still way too slow.

"""

import types

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

    >>> import fixed_width
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

class CatchAllField(Field):
    """A field for special cases.

    The `inputs` argument specifies a list of input field names that
    should cause this one to fire.  If any of those fields is present,
    `function` is called with the entire input record as an argument.

    >>> f = CatchAllField(['x', 'y'], lambda data: data.get('z'))
    >>> m = FieldMapper({'a': f})
    >>> [m.map(x) for x in [{'z': 2}, {'x': 4, 'z': 3}, {'y': 5, 'z': 6},
    ...                     {'x': 7}]]
    ... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [{'original_data': {...}}, {...'a': 3...}, {...'a': 6...}, 
     {...'a': None...}]

    """
    def __init__(self, inputs, function):
        self.inputs, self.function = inputs, function
    def inverteds(self):
        return dict((input, self.function) for input in self.inputs)

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
    field’s aliases, it isn’t included in the fields to copy from.

    """
    def __init__(self, fields):
        self.inverteds = {}
        for name, field in fields.items():
            field = as_field(field)
            for k, v in field.inverteds().items():
                assert k not in self.inverteds, (name, k, field,
                                                 self.inverteds[k])
                self.inverteds[k] = (name, v)
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

if __name__ == '__main__':
    import doctest
    doctest.testmod()
