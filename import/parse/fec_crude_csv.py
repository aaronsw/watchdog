#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Import FEC data.

"""
import csv, sys, cgitb, fixed_width, zipfile, cStringIO, os, glob, time
import codecs, re
from field_mapper import FieldMapper, Reformat, CatchAllField

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

def name_combo(first, middle, last):
    """
    >>> name_combo('John', '', 'Smith')
    'John Smith'
    >>> name_combo('John', 'Buckminster', 'Smith')
    'John Buckminster Smith'
    >>> name_combo('John', 'B', 'Smith')
    'John B. Smith'

    This is probably incorrectly filed, but comes from a filing on
    2006-04-12.  Should we fix it?
    >>> name_combo('Richard E', '', 'Williams')
    'Richard E Williams'

    This is from a filing from 2005-04-12.
    >>> name_combo(' JOE ', '', 'CAPPETTI ')
    ' JOE  CAPPETTI '

    """
    if len(middle) == 1: middle += '.'
    return ' '.join(filter(None, [first, middle, last]))

def caret_separated_name(name):
    """
    Examples from `FEC_v300.rtf`.
    >>> caret_separated_name('Smith^John W.^Dr.^Jr.')
    'Dr. John W. Smith, Jr.'
    >>> caret_separated_name('Smith^John W.^^Jr.')
    'John W. Smith, Jr.'
    >>> caret_separated_name('Smith Medical Corporation')
    'Smith Medical Corporation'
    >>> caret_separated_name('Smith-Reilly^Jennifer T.^Ms.')
    'Ms. Jennifer T. Smith-Reilly'

    Other examples from data:
    >>> caret_separated_name('Field^Tracy C.^^')
    'Tracy C. Field'
    >>> caret_separated_name('Thomson^Linda^Mrs.^')
    'Mrs. Linda Thomson'
    >>> caret_separated_name('Elrod^Adrienne')
    'Adrienne Elrod'

    Should we downcase/titlecase this one?
    >>> caret_separated_name('LOVE^KARA^^')
    'KARA LOVE'
    """
    fields = name.split('^')
    while len(fields) < 4: fields.append('')

    lastname, firstname, prefix, suffix = fields
    if prefix: prefix += ' '
    if firstname: firstname += ' '
    if suffix: suffix = ', ' + suffix

    return ''.join([prefix, firstname, lastname, suffix])

def schedule_type(data):
    """Is this a contribution, an expenditure, or neither?"""
    if data.get('rec_type') == 'TEXT': return # they have an unhelpful form_type
    if data['form_type'].startswith('SA'): return 'contribution'
    if data['form_type'].startswith('SB'): return 'expenditure'

def date(value):
    if value: return fixed_width.date(value)
    return None                         # to keep Postgres happy

fields = {
    'date': Reformat(format=date,
                     source=['date',
                             'date_received',
                             'contribution_date',
                             'expenditure_date',
                             'date_(of_contribution)',
                             'date_(incurred)', # XXX this is for SC loans
                             'date_of_expenditure']),
    'candidate_fec_id': Reformat(format=strip, source=['candidate_fec_id',
                                                       'candidate_id_number',
                                                       'fec_candidate_id_number']),
    'tran_id': ['tran_id', 'transaction_id_number'],
    'occupation': ['occupation', 'contributor_occupation', 'indocc'],
    'contributor_org': ['contributor_org',
                        'contributor_organization_name',
                        'contrib_organization_name'],
    'contributor': [Reformat(format=caret_separated_name,
                             source=['contributor_name']),
                    # XXX should include contributor_prefix and
                    # contributor_suffix?
                    lambda contributor_first_name,
                           contributor_middle_name,
                           contributor_last_name:
                        name_combo(contributor_first_name,
                                   contributor_middle_name,
                                   contributor_last_name),
                    ],
    # XXX recipient_name should be reformatted with caret_separated_name
    # at least in 5.00
    # XXX also 'recipient_first_name' 'recipient_last_name'
    # 'recipient_middle_name' 'recipient_organization_name'
    # 'recipient_prefix' 'recipient_suffix'
    'recipient': ['payee_organization_name', 'recipient_name', 'name_(payee)'],
    'employer': ['employer', 'contributor_employer', 'indemp'],
    'amount': Reformat(format=amount,
                       source=['amount',
                               # XXX 6.x contribution_amount: different format
                               'contribution_amount',
                               'amount_received',
                               'expenditure_amount', # also 6.x
                               'amount_of_expenditure']),
    'address': [lambda street__1, street__2, city, state, zip:
                ' '.join([street__1, street__2, city, state, zip]),
                lambda contributor_street__1, contributor_street__2,
                       contributor_city, contributor_state, contributor_zip:
                ' '.join([contributor_street__1, contributor_street__2,
                          contributor_city, contributor_state, contributor_zip])
                ],

    'committee': ['committee_name', 'committee_name_______', 'committeename'],
    'candidate': [Reformat(format=caret_separated_name,
                           source='candidate_name'),
                  lambda candidate_first_name,
                         candidate_middle_name,
                         candidate_last_name:
                     name_combo(candidate_first_name,
                                candidate_middle_name,
                                candidate_last_name),
                  ],
    'filer_id': ['filer_fec_cand_id',
                 'filer_fec_cmte_id_',
                 'filer_fec_cmte_id',
                 'filer_fec_committee_id',
                 'filer_committee_id_number',
                 'filer_candidate_id_number',
                 "filer's_fec_id_number",
                 'filer_committee_id'],
    
    'type': CatchAllField(['form_type'], schedule_type),
}

fieldmapper = FieldMapper(fields)

def _regrtest_fields():
    """
    Regression tests for the `fields` table.
    
    >>> mapped = fieldmapper.map({'date_received': '20081130',
    ...                                   'tran_id': '12345', 
    ...                                   'weird_field': 34, 
    ...                                   'amount_received': '123456'})
    >>> sorted(mapped.keys())
    ['amount', 'date', 'original_data', 'tran_id']
    >>> mapped['date']
    '2008-11-30'
    >>> mapped['amount']
    '1234.56'
    >>> mapped['original_data']['weird_field']
    34
    >>> mapped['tran_id']
    '12345'
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
    headerdir = os.path.split(__file__)[0]
    if version not in headers_cache:
        headers_cache[version] = \
            headers(os.path.join(headerdir, 'fec_headers', '%s.csv' % version))
    return headers_cache[version]

class ascii28separated(csv.excel):
    """The FEC moved from CSV to chr(28)-separated files in format version 6."""
    delimiter = chr(28)

def translate_to_utf_8(fileobj):
    """Convert a presumably Windows-1252 file to UTF-8.

    Although the FEC’s documents claim non-ASCII characters will be
    rejected, I have seen a filing in Windows-1252.  Aaron points out:
    > The `chardet` library might be useful:
    > <http://chardet.feedparser.org/>
    """
    return codecs.EncodedFile(fileobj, 'utf-8', 'windows-1252')

# Note that normally we are reading from a zipfile, and Python’s
# stupid zipfile interface doesn’t AFAICT give us the option of
# streaming reads — it insists on reading the whole zipfile element at
# once.  So we don’t lose much by parsing from a string rather than a
# file object here, as long as we are careful not to accidentally make
# extra copies of the string.
def readstring(astring):
    # from the Python 2.5 documentation: “Note: This version of the
    # csv module doesn't support Unicode input. Also, there are
    # currently some issues regarding ASCII NUL
    # characters. Accordingly, all input should be UTF-8 or printable
    # ASCII to be safe; see the examples in section 9.1.5. These
    # restrictions will be removed in the future.”
    fileobj = translate_to_utf_8(cStringIO.StringIO(astring))
    r = csv.reader(fileobj)
    headerline = r.next()
    if chr(28) in headerline[0]:
        # it must be in the new FS-separated format
        fileobj.seek(0)
        r = csv.reader(fileobj, dialect=ascii28separated)
        headerline = r.next()
    if len(headerline) == 1:
        # It’s probably the old 2.x format that we don’t support yet
        # because we can’t find docs; return without yielding
        # anything.
        return
    version = headerline[2]
    headermap = headers_for_version(version)

    for line in r:
        if not line: continue         # FILPAC inserts random blank lines
        if line[0].lower().strip() in ('[begintext]', '[begin text]'):
            # see e.g. “New F99 Filing Type for unstructured,
            # formatted text” in FEC_v300.rtf.  Note that this data
            # may violate `csv`'s expectations, so we have to read it
            # ourselves, and rely on `csv` not doing some kind of
            # read-ahead.
            while True:
                line = fileobj.readline().lower()
                if not line: break      # robustness against premature EOF
                if line.strip() in ('[endtext]', '[end text]',
                                    # NGP Campaign Office(R) 1.0e filing 207928
                                    '[endtext]"'
                                    ):
                    break
                # XXX right now we just discard the lines
            line = r.next()
            # There can be a blank line here too, inserted by e.g. NIC
            # WebForms 6.2.1.1 in filing 353794.fec from 20080722.zip.
            if not line: continue
        fieldnames = findkey(headermap, line[0])
        if not fieldnames:
            raise "could not find field defs", (line[0], headermap.keys())
        rv = fieldmapper.map(dict(zip(fieldnames, line)))
        rv['format_version'] = version # for debugging
        yield rv

candidate_name_res = [re.compile(x, re.IGNORECASE) for x in
                      [r'''(?ix)(?P<candidate>.*) \s+ for \s+ congress''',
                       r'''(?ix)friends \s+ of \s+ (?P<candidate>.*)''']]
# maybe also:
#  | committee \s+ to \s+ elect (?P<candidate>.*)
# "Alan Pedigo For US House of Rep"
# These are recipients of a certain PAC’s donations:
# "Citizens for Arlen Specter"
# "Ike Skelton for Congress Committee"
# "Bill Nelson for U.S. Senate Campaign"
# "Martin Frost Campaign Committee"
# "Friends of Connie Morella for Congress Committee"
# "Committee to Elect McHugh"

def warn(string):
    sys.stderr.write(string + "\n")
    sys.stderr.flush()

def read_filing(astring, filename):
    records = readstring(astring)
    form = records.next()
    if not form['original_data']['form_type'].startswith('F'):
        warn("skipping %r: its first record is %r" % (filename, formline))
        return
    form['report_id'] = filename[:-4]
    if not form.get('candidate'):
        for regex in candidate_name_res:
            mo = regex.match(form.get('committee', ''))
            if mo:
                form['candidate'] = mo.group('candidate')
                break
    return form, records

def readfile_zip(filename):
    zf = zipfile.ZipFile(filename)
    for name in zf.namelist():
        yield read_filing(zf.read(name), name)

def readfile_generic(filename):
    if filename.endswith('.zip'):
        return readfile_zip(filename)
    else:
        _, basename = os.path.split(filename)
        return [read_filing(file(filename).read(), basename)]

EFILINGS_PATH = '../data/crawl/fec/electronic/'

def parse_efilings(filepattern = None):
    if filepattern is None: filepattern = EFILINGS_PATH + '*.zip'
    last_time = time.time()
    for filename in glob.glob(filepattern):
        sys.stderr.write('parsing efilings file %s\n' % filename)
        for parsed_file in readfile_generic(filename):
            yield parsed_file
        now = time.time()
        sys.stderr.write('parsing took %.1f seconds\n' % (now - last_time))
        last_time = now

if __name__ == '__main__':
    cgitb.enable(format='text')
    # pprint is unacceptable --- it made the script run 40× slower.
    import simplejson
    for filename in sys.argv[1:]:
        for form, schedules in readfile_generic(filename):
            print simplejson.dumps(form, sort_keys=True, indent=4)
            for schedule in schedules:
                print simplejson.dumps(schedule, sort_keys=True, indent=4)
