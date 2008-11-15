from fixed_width import parse_file, string, date, integer, filler, state, digits

def_5500 = [
  ('unk1_digits', 26, string),
  ('unk2', 8, date),
  ('unk3', 8, date),
  ('unk4', 1, integer),
  ('unk4', 1, integer),
  ('unk4', 1, integer),
  ('unk4', 1, integer),
  ('unk4', 1, integer),
  ('unk4', 1, integer),
  ('unk4', 1, integer),
  ('unk4', 1, integer),
  ('plan_name', 140, string),
  ('unk5', 8, date),
  ('corp_name', 141, string),
  ('street1', 35, string),
  ('street2', 108, string),
  ('city', 22, string),
  ('state', 2, state),
  ('zip', 5, digits),
  ('zip4', 4, digits),
  ('unk6', 3, string),
  (None, 792, filler), # unparsed
  (None, 2, filler('\r\n'))
]

if __name__ == "__main__":
    import tools
    tools.export(parse_file(def_5500, file('../data/crawl/irs/5500/F_5500_2006.txt')))