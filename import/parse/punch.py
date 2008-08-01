from decimal import Decimal
import re
import web

r_row = re.compile(r'<tr>(.*?)</tr>', re.S)
r_td = re.compile(r'<td v[^>]+>([^<]*)</td>')
r_member = re.compile(r'member=([^"]+)">([^<]+)<')

def fixdec(d):
    d = d.strip()
    return Decimal(d) and Decimal(d)/100

def parse_doc(d):
    for row in r_row.findall(d):
        out = r_td.findall(row)
        if out:
            dist, membername = r_member.findall(row)[0]
            dist = dist.replace('At Large', '00')
            dist = dist[:2] + '-' + dist[2:].zfill(2)
            
            s = web.storage()
            s.district = dist
            s.progressive2008 = fixdec(out[0])
            s.chips2008 = fixdec(out[1])
            s.progressiveall = fixdec(out[3])
            s.name = membername.decode('iso-8859-1')
            
            yield s

def parse_all():
    d = file('../data/crawl/punch/house.html').read()
    for x in parse_doc(d): yield x
    d = file('../data/crawl/punch/senate.html').read()
    for x in parse_doc(d): yield x

if __name__ == "__main__":
    import tools
    tools.export(parse_all())