"""
Tools to crawl data from Open Secrets.
"""
import re, urllib

u_lpac = "http://www.opensecrets.org/pacs/industry.php?txt=Q03&cycle=2008"
r_lpac = re.compile(r'<tr>\s*<td><a href="lookup2\.php\?strID=(C\d+)">[^<]+</a>\s*</td><td>\s*<a href="/politicians/summary\.php\?cid=(N\d+)&cycle=2008">')

def lpacs():
    return r_lpac.findall(urllib.urlopen(u_lpac).read())

if __name__ == "__main__":
    listing = lpacs()
    fh = file('../data/crawl/opensecrets/leadership.tsv', 'w')
    fh.write('FECCommID\tCRPCandID\n')
    for item in listing:
        fh.write('%s\t%s\n' % item)
    fh.close()
