import glob
import web
import xmltramp

CANSUM = '../data/crawl/opensecrets/cansum/%s/%s.xml'

class ParseError(Exception): pass

def parse_can(opensecretsid, year=2008):
    out = web.storage()
    out.opensecretsid = opensecretsid

    d = xmltramp.load(CANSUM % (year, opensecretsid))
    out.total = int(d.candidate.totals('total_receipts'))

    for source in d.candidate.totals.sources:
        if source('type') == 'PAC':
            out.business_pac = 0 # in case it doesn't appear
            for sd in source:
                if sd('type') == "Business":
                    out.business_pac = int(sd('total_receipts'))

    bad = 0
    for sector in d.candidate.totals.sectors:
        if sector('name') not in ['Labor']:
            bad += int(sector('pac'))
    out.badmoney = bad

    return out

def parse_all():
    for fn in glob.glob(CANSUM % (2008, '*')):
        opensecretsid = fn.split('/')[-1].split('.')[0]
        try:
            s8 = parse_can(opensecretsid, 2008)
            try:
                s6 = parse_can(opensecretsid, 2006)
            except:
                yield s8
            else:
                s = web.storage()
                s.badmoney = s8.badmoney + s6.badmoney
                s.total = s8.total + s6.total
                s.business_pac = s8.business_pac + s6.business_pac
                yield s
        except:
            print "Could not read", opensecretsid

if __name__ == "__main__":
    import tools
    tools.export(parse_all())
