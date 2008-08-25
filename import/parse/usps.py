"""
Parser for USPS AIS records.
"""

## Types used in definitions

def date(s):
    return s[0:4] + '-' + s[4:6] + '-' + s[6:8]

def year(s):
    return '20' + s

def string(s):
    return s.strip()

def boolean(s):
    return {'Y': True, 'N': False, ' ': None}[s]

def halfbool1(s):
    return dict(A=True, B=True, C=False, D=False)

def halfbool2(s):
    return dict(A=True, B=False, C=True, D=False)

filler = string

def enum(s=None, **db):
    if isinstance(s, basestring):
        return string(s)
    else:
        if ' ' not in db: db[' '] = None
        return lambda s: db[s]

oddeven = enum(O='ODD', E='EVEN', B='BOTH')

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

## The definitions

def def_copyright(n):
    return [
      ('_type', 1, lambda s: 'File Header'),
      (None, 5, filler),
      ('copyright_statement', 12, string),
      (None, 1, filler),
      ('month', 2, integer),
      (None, 1, filler),
      ('year', 2, year),
      (None, 1, filler),
      ('copyright_owner', 4, string),
      (None, 1, filler),
      ('volume_seq', 3, integer),
      (None, n, filler)
    ]

def_ctystate = {
  'C': def_copyright(96),
  'S': [
    ('_type', 1, lambda s: 'ZIP Scheme Combination'),
    ('label_zip', 5, string),
    ('combined_zip', 5, string),
    (None, 118, filler)
  ],
  'A': [
    ('_type', 1, lambda s: 'Street Alias'),
    ('zip', 5, string),
    ('alias_street_pre_direction', 2, string),
    ('alias_street_name', 28, string),
    ('alias_street_suffix', 4, string),
    ('alias_street_post_suffix', 2, string),
    ('street_pre_direction', 2, string),
    ('street_name', 28, string),
    ('street_suffix', 4, string),
    ('street_post_suffix', 2, string),
    ('alias_type', 1, enum(
      A='ABBREVIATED', 
      C='STREET NAME CHANGED', 
      O='NICKNAME/OTHER', 
      P='PREFERRED STREET NAME'
    )),
    ('alias_date', 8, date),
    ('delivery_low', 10, string),
    ('delivery_high', 10, string),
    ('odd_even', 1, oddeven),
    (None, 21, filler)
  ],
  'Z': [
    ('_type', 1, lambda s: 'Zone Split'),
    ('old_zip', 5, string),
    ('old_route', 4, string),
    ('new_zip', 5, string),
    ('new_route', 4, string),
    ('date', 8, date),
    (None, 102, filler)
  ],
  'D': [
    ('_type', 1, lambda s: 'ZIP City State'),
    ('zip', 5, string),
    ('city_state_key', 6, string),
    ('zip_class_code', 1, enum(**{
      ' ': 'NON-UNIQUE',
      'M': 'AFO/FPO/DPO MILITARY',
      'P': 'PO BOX ZIP',
      'U': 'UNIQUE ZIP'
    })),
    ('city_state_name', 28, string),
    ('city_state_abbrev', 13, string),
    ('facility_code', 1, enum(
      B='BRANCH',
      C='COMMUNITY POST OFFICE',
      N='NON-POSTAL COMMUNITY NAME, FORMER POSTAL FACILITY, OR PLACE NAME',
      P='POST OFFICE',
      S='STATION',
      U='URBANIZATION'
    )),
    ('mailing_name', 1, boolean),
    ('preferred_last_line_key', 6, string),
    ('preferred_last_line_name', 28, string),
    ('city_delivery', 1, boolean),
    ('carrier_route_sort_rate', 1, halfbool1),
    ('merging_permitted', -1, halfbool2),
    ('unique_zip_name', 1, boolean),
    ('finance_no', 6, string),
    ('state_abbrev', 2, string),
    ('county_no', 3, string),
    ('county_name', 25, string)
  ],
  'N': [
    ('_type', 1, lambda s: 'Seasonal'),
    ('zip', 5, string),
    ('jan', 1, boolean),
    ('feb', 1, boolean),
    ('mar', 1, boolean),
    ('apr', 1, boolean),
    ('may', 1, boolean),
    ('jun', 1, boolean),
    ('jul', 1, boolean),
    ('aug', 1, boolean),
    ('sep', 1, boolean),
    ('oct', 1, boolean),
    ('nov', 1, boolean),
    ('dec', 1, boolean),
    (None, 111, filler)
  ]
}

def_5digit = {
  'C': def_copyright(62),
  'D': [
    ('_type', 1, lambda s: "Five-Digit ZIP Detail"),
    ('zip', 5, string),
    ('update_key', 10, string),
    ('action_code', 1, enum(A="ADD", D="DELETE")),
    ('record_type', 1, enum(
      G='GENERAL DELIVERY',
      P='PO BOX',
      R='RURAL ROUTE/HIGHWAY CONTRACT',
      S='STREET'
    )),
    ('street_pre_dir', 2, string),
    ('street_name', 28, string),
    ('street_suffix', 4, string),
    ('street_post_dir', 2, string),
    ('addr_primary_lo', 10, string),
    ('addr_primary_hi', 10, string),
    ('addr_primary_odd_even', 1, oddeven),
    ('finance_no', 6, string),
    ('state_abbrev', 2, string),
    ('urbanization_ctyst_key', 6, string),
    ('prefd_lastline_ctyst_key', 6, string)
  ]
}

def_zip4 = {
  'C': def_copyright(149),
  'D': [
    ('_type', 1, lambda s: "ZIP+4 Detail"),
    ('zip', 5, string),
    ('update_key', 10, integer), #?
    ('action', 1, enum(A='ADD', D='DELETE')),
    ('record_type', 1, enum(
      F='FIRM',
      G='GENERAL DELIVERY',
      H='HIGH-RISE',
      P='PO BOX',
      R='RURAL ROUTE/HIGHWAY CONTRACT',
      S='STREET'
    )),
    ('carrier_route_id', 4, string),
    ('street_pre_dir', 2, string),
    ('street_name', 28, string),
    ('street_suffix', 4, string),
    ('street_post_dir', 2, string),
    ('addr_primary_lo', 10, string),
    ('addr_primary_hi', 10, string),
    ('addr_primary_odd_even', 1, oddeven),
    ('building_or_firm_name', 40, string),
    ('addr_secondary_abbrev', 4, string),
    ('addr_secondary_low', 8, string),
    ('addr_secondary_high', 8, string),
    ('addr_secondary_odd_even', 1, oddeven),
    ('zip4_lo', 4, string),
    ('zip4_hi', 4, string),
    ('base_alt', 1, enum(B='BASE', A='ALTERNATIVE')),
    ('lacs_status', 1, enum(L='LACS CONVERTED')),
    ('govt_bldg', 1, enum(
      A='CITY GOV BLDG',
      B='FEDERAL GOV BLDG',
      C='STATE GOV BLDG',
      D='FIRM ONLY',
      E='CITY GOV BLDG AND FIRM ONLY',
      F='FED GOV BLDG',
      G='STATE GOV BLDG AND FIRM ONLY'
    )),
    ('finance_no', 6, string),
    ('state_abbrev', 2, string),
    ('county_no', 3, string),
    ('congress_dist', 2, string),
    ('municipality_ctyst_key', 6, string),
    ('urbanization_ctyst_key', 6, string),
    ('prefd_lastline_ctyst_key', 6, string)
  ]
}

def_tigerdat = [
  ('_type', 0, lambda s: "Census/USPS County Map"),
  ('state_code', 2, string),
  ('state_abbrev', 2, string),
  ('county_code', 3, string),
  ('county_name', 25, string),
  (None, 2, filler)
]

def_tigerzip = {
  'C': [
    ('_type', 0, lambda s: 'File Header'),
    (None, 5, filler),
    ('year', 4, integer),
    ('month', 2, integer),
    ('copyright_statement', 16, string),
    (None, 59, filler), # not really there, it seems
    (None, 2, filler) # CRLF
  ],
  'D': [
    ('_type', 0, lambda s: 'TIGER/ZIP Data'),
    ('zip', 5, string),
    ('zip4', 4, string),
    ('tlid', 10, string),
    ('carrier_route', 4, string),
    ('state_code', 2, string),
    ('county_code', 3, string),
    ('right_left', 1, enum(R='RIGHT', L='LEFT', B='BOTH')),
    ('census_tract', 6, string),
    ('census_block', 4, string),
    ('from_lat', 9, string),
    ('from_long', 10, string),
    ('to_lat', 9, string),
    ('to_long', 10, string),
    ('pmsa', 4, string),
    ('cmsa', 4, string),
    ('multimatch', 1, boolean),
    (None, 2, filler)
  ]
}

def parse_line(linedef, line):
    out = {}
    n = 0
    for (k, l, t) in linedef:
        if l < 0 : # go back
            out[k] = t(line[n+l:n])
        elif k is not None:
            out[k] = t(line[n:n+l])
        if l > 0: n += l
    return out

def get_len(filedef):
    linelen = set(sum(line[FIELD_LEN] for line in kind if line[FIELD_LEN] > 0) for kind in filedef.itervalues())
    assert len(linelen) == 1, [(kind_name, sum(line[FIELD_LEN] for line in kind if line[FIELD_LEN] > 0)) for kind_name, kind in filedef.iteritems()]
    linelen = list(linelen)[0]
    return linelen

## The functions you might want to call

def parse_file(filedef, fh):
    linelen = get_len(filedef)
    for line in iter(lambda: fh.read(linelen), ''):
        yield parse_line(filedef[line[0]], line)

def parse_tigerzip(fh):
    linelen = get_len(def_tigerzip)
    for line in fh:
        if line.startswith(' ' * 5):
            t = 'C'
        else:
            t = 'D'

        yield parse_line(def_tigerzip[t], line)

def parse_tigerdat(fh):
    for line in fh:
        yield parse_line(def_tigerdat, line)

def parse_zip2dist(fh):
    for row in parse_file(def_zip4, fh):
        if row['_type'] != 'ZIP+4 Detail': continue
        if row['congress_dist'] == 'AL':
            row['congress_dist'] = '00'
        if row['zip4_lo'] == row['zip4_hi']:
            zip4s = [row['zip4_lo']]
        else:
            zip4s = [str(x).zfill(4) for x in xrange(int(row['zip4_lo']), int(row['zip4_hi']) + 1)]
        for zip4 in zip4s:
            yield row['zip'] + '-' + zip4, row['state_abbrev'] + '-' + row['congress_dist']

if __name__ == "__main__":
    import sys, glob, tools
    
    def_map = {'--ctystate': def_ctystate, '--5digit': def_5digit, '--zip4': def_zip4}
    
    if sys.argv[1] in def_map:
        for fn in glob.glob(sys.argv[2] + '*.txt'):
            tools.export(parse_file(def_map[sys.argv[1]], file(fn)))
    elif sys.argv[1] == '--tiger':
        for fn in glob.glob(sys.argv[2] + '*/*.txt'):
            tools.export(parse_tigerzip(file(fn)))
    elif sys.argv[1] == '--tigerdat':
        for fn in glob.glob(sys.argv[2] + '*/TIGER.DAT'):
            tools.export(parse_tigerdat(file(fn)))
