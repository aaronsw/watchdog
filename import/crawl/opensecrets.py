"""
Tools to crawl data from Open Secrets.
"""
import re, urllib, os

DATA_DIR = "../data/"

u_lpac = "http://www.opensecrets.org/pacs/industry.php?txt=Q03&cycle=2008"
r_lpac = re.compile(r'<tr>\s*<td><a href="lookup2\.php\?strID=(C\d+)">[^<]+</a>\s*</td><td>\s*<a href="/politicians/summary\.php\?cid=(N\d+)&cycle=2008">')

def lpacs():
    return r_lpac.findall(urllib.urlopen(u_lpac).read())

def write_lpacs():
    listing = lpacs()
    fh = file(DATA_DIR + 'crawl/opensecrets/leadership.tsv', 'w')
    fh.write('FECCommID\tCRPCandID\n')
    for item in listing:
        fh.write('%s\t%s\n' % item)
    fh.close()

u_cands = "http://www.opensecrets.org/politicians/candlist.php?congno=110"
r_candid = re.compile(r"summary\.php\?cid=([A-Z0-9]+)&cycle=\d+\" ?>([^<]+)")
u_sectors = "http://www.opensecrets.org/politicians/pop_sector.php?cycle=2008&cid=%s"

import sys
def count(x):
    lenx = len(x)
    for n, y in enumerate(x):
        sys.stderr.write('\r%s/%s = %s' % (n, lenx, float(n)/lenx))
        yield y

def sectors():
    cands = set(x[0] for x in r_candid.findall(urllib.urlopen(u_cands).read()))
    for cand in count(list(cands)):
        pth = DATA_DIR + 'crawl/opensecrets/sectors/%s.html' % cand
        if os.path.exists(pth): continue
        file(pth, 'w').write(urllib.urlopen(u_sectors % cand).read())
        time.sleep(3)
    

fhout = file('canids.tsv', 'w')
fhout.write('opensecretsid\tname\n')
for k, v in x:
    fhout.write('%s\t%s\n' % (k, v.replace('  ', '')))

fhout.close()

if __name__ == "__main__":
    write_lpacs()
