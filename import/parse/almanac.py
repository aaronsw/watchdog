#!/usr/bin/python
# Scrape nationaljournal.com pages.
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

def extract_text(html):
    html = re.sub(r'(?i)<br[^>]*>', '\n', html)
    soup = BeautifulSoup.BeautifulSoup(html, convertEntities='html')
    text = ''.join(soup.findAll(text=True))
    text = text.replace(u'\xa0', ' ')   # &nbsp;
    return text.strip()

def plain(fieldname):
    "A plain text field."
    def handle(rv, html):
        rv[fieldname] = extract_text(html)
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
                cell_value = extract_text(str(cell))
                if cell_value != '':
                    current_row[headers[col]] = cell_value
                    actually_got_something = True
        #print current_row
        last_election_value = current_row['election']
        if actually_got_something: results.append(current_row)
    rv['electionresults'] = results

def _parse_list(html):
    soup = BeautifulSoup.BeautifulSoup(html)
    hash = {}
    for li in soup('li'):
        name = li.b.string
        if name is None: continue # no bold text, prolly not a name-val pair
        name = name.strip()
        if name.endswith(':'): name = name[:-1]
        hash[name] = extract_text(str(li.b.nextSibling))
    # original version (which didn't cope well with capitalized and
    # unclosed LI tags, etc.)
    #     for mo in re.finditer(r'<li><b>(.*?): ?</b> (.*?)</li>', html):
    #         hash[mo.group(1)] = mo.group(2)
    return hash

def parse_list(name):
    def func(rv, html):
        rv[name] = _parse_list(html)
    return func

# Things we care about if they are in the left column of a 2-column
# table, or if they are headers.
person_fields = {
    'Born': plain('born'),
    'Home': plain('home'),
    'Education': plain('education'),
    'Religion': plain('religion'),
    'Marital Status': plain('maritalstatus'),
    'Elected Office': plain('office'),
    'DC Office': plain('dcoffice'),
    'State Offices': plain('stateoffice'),
    'Committees': plain('committees'),
    'District Demographics': parse_list('demographics'),
    'Election Results': election_table,
}
state_fields = {
    'The State': parse_list('state'),
}
        
def scrape_by_headers(rv, fields, html):
    "Find sections of text underneath certain headers with special meanings."
    # They changed from #6666CC to #333366 after 2002, although the
    # more recent page elements ("Go Wireless") are #333366 even on old
    # pages, leading to a kind of inconsistent appearance.
    by_headers = re.split(r' color="#(?:6666CC|333366)"[^>]*>', html)

    for item in by_headers:
        for key in fields.keys():
            if item.startswith(key):
                # </UL> is a special case for "District Demographics"
                # and "The State"
                mo = re.search(r'(?is)</font>(.*?)(?:</UL>|</p>)', item)
                if mo: fields[key](rv, mo.group(1))

def scrape_table(rv, fields, html):
    tablerows = re.findall(r'(?is)<tr [^>]*>.*?</tr>', html)

    for row in tablerows:
        cells = re.findall(r'(?is)<td [^>]*>(.*?)</td>', row)
        if len(cells) != 2: continue
        name = re.sub(':$', '', extract_text(cells[0]))
        if fields.has_key(name): fields[name](rv, cells[1])
        
def scrape_person(fname):
    fo = file(fname)
    rv = {'filename': fname}
    contents = fo.read()

    photo_alt = re.search(r'<img [^>]*height="?(?:128|117)["\s][^>]*' +
                          r'alt="(?P<alt>[^"]*)',
                          contents)
    if photo_alt is not None:
        scrape_photo_alt(fname, rv, photo_alt.group('alt'))
    else: rv['no_photo_found'] = True

    scrape_by_headers(rv, person_fields, contents)
    scrape_table(rv, person_fields, contents)

    return rv

def scrape_state_demographics(rv, html):
    income_section = re.search(r'<b>Household Income: </b>(.*\&middot.*?)<LI>', html)
    if not income_section: return
    items = income_section.group(1)
    rv.setdefault('state', {})
    median = re.search(r'Median:&nbsp;(\$[\d,]+) ', items)
    if median: rv['state']['Median income'] = median.group(1)
    poverty = re.search(r'Poverty status:&nbsp;([\d.]+%)', items)
    if poverty: rv['state']['Poverty status'] = poverty.group(1)

def scrape_state(fname):
    fo = file(fname)
    rv = {'filename': fname}
    contents = fo.read()
    scrape_by_headers(rv, state_fields, contents)
    scrape_state_demographics(rv, contents)
    return rv

def main(files):
    import pprint
    if not files: raise "usage: %s foo.html [bar.html ...]" % sys.argv[0]
    for fname in files:
        print "%s as person:" % fname
        print pprint.pprint(scrape_person(fname))
        print "%s as state:" % fname
        print pprint.pprint(scrape_state(fname))

if __name__ == '__main__': main(sys.argv[1:])
