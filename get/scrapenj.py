#!/usr/bin/python
# Scrape nationaljournal.com pages.
import sys
sys.path.append('/usr/share/pycentral/python-syck/site-packages')
import re, BeautifulSoup, sys

def scrape_photo_alt(fname, rv, alt):
    "Interpret the alt text of the portrait photos from most pages."
    # special case for
    # nationaljournal.com/pubs/almanac/2000/people/president.htm
    if alt == 'photo': return 
    photo_parts = re.match(r'((?P<title>Rep\.|Sen\.|Gov\.|Del\.) )?' +
                           '(?P<name>.*?)' +
                           r' \((?P<party>(D|R|DFL|I|IR|ID|Ind))' +
                              r'(-At Large)?\)',
                           alt)
    if photo_parts is None:
        raise "couldn't understand caption " + alt + " in " + fname
    for field in 'name party title'.split():
        rv[field] = photo_parts.group(field)

tag = '(?:<[^>]+>)'
tags = tag + '*'
def crappy_extract_text(html):
    value = html
    value = re.sub(r'(?i)<br[^>]*>', '\n', value)
    value = re.sub(tags, '', value)
    value = re.sub(r'(\s|&nbsp;)+', ' ', value)
    value = re.sub(r'&ndash;', '-', value)
    value = re.sub(r'&amp;', '&', value)
    value = re.sub(r'(?s)^\s+', '', value)
    value = re.sub(r'(?s)\s+$', '', value)
    return value

def plain(fieldname):
    "A plain text field."
    def handle(rv, html):
        rv[fieldname] = crappy_extract_text(html)
    return handle

def html(fieldname):
    "A field where we get all the HTML, for debugging."
    def handle(rv, html):
        rv[fieldname] = html
    return handle

def combine(fielda, fieldb):
    "A field with more than one kind of processing, for debugging."
    def handle(rv, html):
        fielda(rv, html)
        fieldb(rv, html)
    return handle

def election_table(rv, html):
    soup = BeautifulSoup.BeautifulSoup('<table><tr><td>' + html)
    headers = {0: 'election'}
    other_headers = {'Candidate': 'candidate', 'Total Votes': 'totalvotes',
                     'Percent': 'percent', 'Expenditures': 'expenditures'}
    results = []
    last_election_value = 'unknown election'
    for row in soup('tr'):
        if len(row('td')) < 2: continue
        current_row = {'election': last_election_value}
        actually_got_something = False
        for cell, col in zip(row('td'), range(100)): # won't have >100 columns!
            # underlined text in the headers
            if cell('u'): headers[col] = other_headers[cell.u.string]
            else: 
                if not headers.has_key(col):
                    # this happens in
                    # e.g. almanac/nationaljournal.com/pubs/almanac/2002/people/mn/mngv.htm
                    continue
                cell_value = crappy_extract_text(str(cell))
                if cell_value != '':
                    current_row[headers[col]] = cell_value
                    actually_got_something = True
        #print current_row
        last_election_value = current_row['election']
        if actually_got_something: results.append(current_row)
    rv['electionresults'] = results

def demographics(rv, html):
    soup = BeautifulSoup.BeautifulSoup(html)
    demographics = {}
    for li in soup('li'):
        name = li.b.string
        if name is None: continue
        name = name.strip()
        assert name.endswith(':'), name
        demographics[name[:-1]] = crappy_extract_text(str(li.b.nextSibling))
    # original version (which didn't cope well with capitalized and
    # unclosed LI tags, etc.)
    #     for mo in re.finditer(r'<li><b>(.*?): ?</b> (.*?)</li>', html):
    #         demographics[mo.group(1)] = mo.group(2)
    rv['demographics'] = demographics

# Things we care about if they are in the left column of a 2-column
# table, or if they are headers.
we_care = {
    'Born': plain('born'),
    'Home': plain('home'),
    'Education': plain('education'),
    'Religion': plain('religion'),
    'Marital Status': plain('maritalstatus'),
    'Elected Office': plain('office'),
    'DC Office': plain('dcoffice'),
    'State Offices': plain('stateoffice'),
    'Committees': plain('committees'),
    'District Demographics': demographics,
    'Election Results': election_table,
}
        
def scrape_by_headers(rv, html):
    "Find sections of text underneath certain headers with special meanings."
    # They changed from #6666CC to #333366 after 2002, although the
    # more recent page elements ("Go Wireless") are #333366 even on old
    # pages, leading to a kind of inconsistent appearance.
    by_headers = re.split(r' color="#(?:6666CC|333366)"[^>]*>', html)

    for item in by_headers:
        for key in we_care.keys():
            if item.startswith(key):
                # </UL> is a special case for District Demographics
                mo = re.search(r'(?is)</font>(.*?)(?:</UL>|</p>)', item)
                if mo: we_care[key](rv, mo.group(1))

def scrape_table(rv, html):
    tablerows = re.findall(r'(?is)<tr [^>]*>.*?</tr>', html)

    for row in tablerows:
        cells = re.findall(r'(?is)<td [^>]*>(.*?)</td>', row)
        if len(cells) != 2: continue
        name = re.sub(':$', '', crappy_extract_text(cells[0]))
        if we_care.has_key(name):
            we_care[name](rv, cells[1])
        

def scrape1(fname):
    fo = file(fname)
    rv = {'filename': fname}
    contents = fo.read()
    photo_alt = re.search(r'<img [^>]*height="?(?:128|117)["\s][^>]*' +
                          r'alt="(?P<alt>[^"]*)',
                          contents)
    if photo_alt is not None:
        scrape_photo_alt(fname, rv, photo_alt.group('alt'))
    else: rv['no_photo_found'] = True
    scrape_by_headers(rv, contents)
    scrape_table(rv, contents)
    return rv

def main(files):
    import pprint
    if not files: raise "usage: %s foo.html [bar.html ...]" % sys.argv[0]
    for fname in files: print pprint.pprint(scrape1(fname))

if __name__ == '__main__': main(sys.argv[1:])
