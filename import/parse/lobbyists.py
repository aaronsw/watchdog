import glob, re, sys
from xml.dom import minidom
from pprint import pprint, pformat

import web

ZIPFILE='../data/crawl/house/lobby/2008_MidYear_XML.zip'
HOUSE_FILES='../data/crawl/house/lobby/*.xml'

def cleanint(n):
    for c in ', %$':
        n = n.replace(c, '')
    return n

def fixbool(x):
    if x == 'true': x = True
    elif x == 'false': x = False
    return x

# HACK: There is only one invalid date (02/31/2008) in the current data set.
#       Lets just set it to Null for now. A beter solution might be to parse
#       the dates here and check that set ones that don't parse to None.
def fixdate(x):
    if '02/31/2008' in x:
        return None
    return x

xml_schema = {
    'filerType': None,
    'organizationName': None,
    'lobbyistPrefix': None,
    'lobbyistFirstName': None,
    'lobbyistMiddleName': None,
    'lobbyistLastName': None,
    'lobbyistSuffix': None,
    'contactName': None,
    'senateRegID': None,
    'houseRegID': None,
    'reportYear': None,
    'reportType': None,
    'amendment': fixbool,
    'signedDate': fixdate,
    'certifiedcontent': fixbool,
    'noContributions': fixbool,
    'comments': None,
    'pacs': { 
        'pac': {
            'name': None
     } },
    'contributions': { 
        'contribution': {
            'type': None, 
            'contributorName': None, 
            'payeeName': None, 
            'recipientName': None, 
            'amount': cleanint, 
            'date': fixdate
    } },
}


def _parse_house_lobbyist(node, sch):
    #out = web.storage()
    out = {}
    for t, s in sch.items():
        elms = node.getElementsByTagName(t)
        for n in elms:
            if hasattr(n, 'firstChild') and n.firstChild:
                if t in out:
                    if not isinstance(out[t], list):
                        out[t] = [out[t]]
                    add_item = lambda x: (out[t].append(x) if x else None)
                else:
                    add_item = lambda x: (out.setdefault(t,x) if x else None)
                if not s:
                    add_item(n.firstChild.data.strip())
                elif callable(s):
                    add_item(s(n.firstChild.data.strip()))
                else:
                    add_item(_parse_house_lobbyist(n, s))
    if 'contribution' in out: return out['contribution']
    if 'pac' in out: return out['pac']
    return out


fileid_regex = re.compile(r'.*?([0-9]*)\.xml')
def parse_house_lobbyists():
    files = glob.glob(HOUSE_FILES)
    parse = lambda f: minidom.parse(f)
    if not files:
        import zipfile
        zf = zipfile.ZipFile(ZIPFILE)
        files = zf.namelist()
        parse = lambda f: minidom.parseString(zf.read(f))
    for f in files:
        print f
        dom = parse(f)
        out = _parse_house_lobbyist(dom, xml_schema)
        out['file_id'] = fileid_regex.match(f).group(1)
        yield out


if __name__ == "__main__":
    for x in parse_house_lobbyists():
        pprint(x)


