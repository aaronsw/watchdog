"""
Parse IRS' political organizations' form download.
"""
import warnings
import web
from fixed_width import string, integer, date, filler, enum, state, digits

olddate = date
def date(s):
    out = olddate(s)
    if out == '--': return None
    else: return out

boolean = enum(**{'1': True, '0': False, '': None})

pipe = (None, 1, filler('|'))

def def_address(name): 
    return [
      (name + '_address_1', string),
      (name + '_address_2', string),
      (name + '_address_city', string),
      (name + '_address_state', state),
      (name + '_address_zip', digits),
      (name + '_address_zip4', digits)
    ]


def_entity = [
  ('form_id', integer),
  ('entity_id', integer),
  ('org_name', string),
  ('ein', digits),
  ('entity_name', string),
  ('entity_tile', string),
] + def_address('entity')

def_polorgs = {
  'H': [
    ('_type', lambda s: 'Header'),
    ('transmission_date', date),
    ('transmission_time', string), #@@
    ('file_type', enum)
  ],
  '1': [
    ('_type', lambda s: '8871 Record'),
    ('form_type', integer), # == 8871
    ('form_id', integer),
    ('initial_report', boolean),
    ('amended_report', boolean),
    ('final_report', boolean),
    ('ein', digits),
    ('org_name', string),
  ] + def_address('mailing') + [
    ('email', string),
    ('established_date', date),
    ('custodian_name', string),
    ] + def_address('custodian') + [
    ('contact_name', string),
    ] + def_address('contact') 
      + def_address('business') + [
    ('exempt_8872', boolean),
    ('exempt_state', string),
    ('exempt_990', boolean),
    ('purpose', string),
    ('material_change_date', date),
    ('insert_datetime', string), #@@
    ('related_entity_bypass', boolean),
    ('eain_bypass', boolean)
  ],
  'D': [('_type', lambda s: 'Director')] + def_entity,
  'R': [('_type', lambda s: 'Related Entity')] + def_entity,
  'E': [
    ('_type', lambda s: 'Election Authority Identification Number (EAIN)'),
    ('form_id', integer),
    ('eain_id', integer),
    ('eain', string),
    ('state_issued', string)
  ],
  '2': [
    ('_type', lambda s: '8872 Record'),
    ('form_type', integer), # == 8872
    ('form_id', integer),
    ('period_begin_date', date),
    ('period_end_date', date),
    ('initial_report', boolean),
    ('amended_report', boolean),
    ('final_report', boolean),
    ('change_of_address', boolean),
    ('org_name', string),
    ('ein', digits),
    ] + def_address('mailing') + [
    ('email', string),
    ('established_date', date),
    ('custodian_name', string),
    ] + def_address('custodian') + [
    ('contact_name', string),
    ] + def_address('contact') 
      + def_address('business') + [
    ('quarter', enum), #?!
    #enum(
    #  a='First Quarterly', 
    #  b='Second Quarterly', 
    #  c='Third Quarterly',
    #  d='Year-End', 
    #  e='Mid-Year', 
    #  f='Monthly', 
    #  g='Pre-election', 
    #  h='Post-election')
    ('monthly_report_month', string),
    ('pre_election_type', string),
    ('pre_or_post_election_date', date),
    ('pre_or_post_election_state', string),
    ('sched_a', boolean),
    ('total_sched_a', integer),
    ('sched_b', boolean),
    ('total_sched_b', integer),
    ('insert_datetime', string), #@@
  ],
  'A': [
    ('_type', lambda s: 'Schedule A'),
    ('form_id', integer),
    ('schedule_a_id', integer),
    ('org_name', string),
    ('ein', digits),
    ('contributor_name', string),
  ] + def_address('contributor') + [
    ('contributor_employer', string),
    ('contribution_amount', string),
    ('contributor_occupation', string),
    ('agg_contribution_ytd', string), #@@float?
    ('contribution_date', date)
  ],
  'B': [
    ('_type', lambda s: 'Schedule B'),
    ('form_id', integer),
    ('schedule_b_id', integer),
    ('org_name', string),
    ('ein', digits),
    ('recipient_name', string),
  ] + def_address('recipient') + [
    ('recipient_employer', string),
    ('expenditure_amount', string),
    ('recipient_occupation', string),
    ('expenditure_date', date),
    ('expenditure_purpose', string)
  ],
  'F': [
    ('_type', 'Footer'),
    ('transmission_date', date),
    ('transmission_time', string), #@@
    ('record_count', integer)
  ]
}

def parse_line(s):
    if s[0] in def_polorgs:
        return parse_line_type(s.strip(), def_polorgs[s[0]])
    else:
        warnings.warn("Don't recognize: " + s[0])

def parse_line_type(line, def4type):
    out = web.storage()
    for (name, kind), val in zip(def4type, line.split('|')):
        out[name] = kind(val)
        print name, val, kind(val)
    return out

def parse_doc(doc):
    for line in doc: yield parse_line(line)

if __name__ == "__main__":
    import tools
    tools.export(parse_doc(file('../data/crawl/irs/pol/FullDataFile.txt')))