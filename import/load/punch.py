from parse import punch
import tools
from settings import db

for can in punch.parse_all():
    d = tools.districtp(can.district)
    if d and can.name.split(',')[0].lower() in d:
        db.update('politician', where='id = $d', vars=locals(),
          chips2008=can.chips2008,
          progressive2008=can.progressive2008,
          progressiveall=can.progressiveall)
