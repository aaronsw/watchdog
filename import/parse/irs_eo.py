from fixed_width import integer, string, date, filler, parse_file, enum, state, digits

def integer2(s): return integer(s[-1] + s[:-1])

def_eo = [
  ('_type', 0, lambda s: 'Exempt Organization'),
  ('ein', 9-0, digits),
  ('primary_name', 79-9, string),
  ('careof_name', 114-79, string),
  ('street', 149-114, string),
  ('city', 171-149, string),
  ('state', 173-171, state),
  ('zip', 183-173, digits),
  ('group_exemption_num', 187-183, integer),
  ('subsection_code', 189-187, string),
  ('affiliation', 1, enum),
  ('classification_code', 194-190, string),
  ('ruling_date', 200-194, date),
  ('deductibility_code', 1, string),  
  ('foundation_code', 2, string),  
  ('activity_code', 212-203, string),  
  ('organization_code', 1, string),  
  ('exempt_org_status_code', 2, string),  
  ('advance_ruling_expiration', 221-215, date),  
  ('tax_period', 227-221, string),  
  ('asset_code', 1, string),  
  ('income_code', 1, string),  
  ('filing_requirement_code', 3, string),  
  (None, 3, filler),  
  ('accounting_period', 2, string),  
  ('asset_amt', 250-237, integer),  
  ('income_amt', 264-250, integer2),  
  ('form_990_revenue_amt', 278-264, integer2),  
  ('ntee_code', 282-278, string),  
  ('sort_name', 318-282, string),
  (None, 2, filler('\r\n'))

]

if __name__ == "__main__":
    import glob
    import tools
    for fn in glob.glob('../data/crawl/irs/eo/*.LST'):
        tools.export(parse_file(def_eo, file(fn)))
