"""
Load data from opensecrets.
"""
from parse import opensecrets
import tools
from settings import db

for can in opensecrets.parse_all():
    p = tools.opensecretsp(can.get('opensecretsid'))
    if p and can:
        db.update('politician', where='id = $p', vars=locals(),
          pct_pac_business=can.business_pac/float(can.total),
          #pct_badmoney = can.badmoney/float(can.total)
        )
