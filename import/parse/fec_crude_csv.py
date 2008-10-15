#!/usr/bin/python
import csv, sys, cgitb, fixed_width
"""
This is just some test code right now for exploring the space of
parsing FEC CSV files in a relatively version-flexible way.

As I write this, it takes about 50% more CPU time than the old version
that was chewing through 300 kilobytes per second on my 700MHz
dinosaur --- now it's doing 210 kilobytes per second.

"""

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
    """
    A class that manifests a tiny DSEL for describing field mappings.

    >>> Field().formatted_with(fixed_width.date) \
               .aka('bob').get_from('dan', {'bob': '20080930'})
    '2008-09-30'
    >>> Field().formatted_with(fixed_width.date) \
               .aka('bob').get_from('dan', {'dan': '20080830'})
    '2008-08-30'
    >>> Field().aka('bob').aka('fred').aliases()
    set(['bob', 'fred'])
    """
    def __init__(self, aliases=set(), formatter=lambda x: x):
        self._aliases = aliases
        self._formatter = formatter
    def formatted_with(self, formatter):
        return Field(aliases=self._aliases, formatter=formatter)
    def aka(self, alias):
        return Field(aliases=self._aliases | set([alias]), formatter=self._formatter)
    def aliases(self):
        return self._aliases
    def get_from(self, name, data):
        for k in [name] + list(self.aliases()):
            if k in data:
                return self._formatter(data[k])

field = Field()

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
    'date': field.formatted_with(fixed_width.date).aka('date_received')
                                                  .aka('contribution_date'),
    'candidate_fec_id': field.formatted_with(strip)
                             .aka('candidate_id_number')
                             .aka('fec_candidate_id_number'),
    'tran_id': field.aka('transaction_id_number'),
    'occupation': field.aka('contributor_occupation'),
    'contributor_org': field.aka('contributor_organization_name')
                            .aka('contrib_organization_name'),
    'employer': field.aka('contributor_employer'),
    'amount': field.formatted_with(amount)
                   .aka('contribution_amount')
                   .aka('amount_received')
                   .aka('expenditure_amount')
                   .aka('amount_of_expenditure'),
}

def map_fields(fields, data):
    """
    >>> mapped = map_fields(fields, {'date_received': '20081131', \
                                     'tran_id': '12345', \
                                     'weird_field': 34, \
                                     'amount_received': '123456'})
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
    rv = {'original_data': data}
    for name, field in fields.items():
        val = field.get_from(name, data)
        if val is not None: rv[name] = val
    return rv

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
    while key:
        if key in hmap: return hmap[key]
        else: key = key[:-1]
def readfile(filename):
    r = csv.reader(file(filename))
    headerline = r.next()
    headermap = headers('../data/crawl/fec/electronic/headers/%s.csv' % headerline[2])
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
            yield map_fields(fields, dict(zip(fieldnames, line)))
        elif in_text_field:
            # XXX currently discard the contents of text fields
            if line[0].lower() == '[endtext]':
                in_text_field = False

if __name__ == '__main__':
    cgitb.enable(format='text')
    for filename in sys.argv[1:]:
        for line in readfile(filename): print line
