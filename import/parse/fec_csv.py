"""
Parser for FEC electronic filings.
"""
__author__ = ["Simon Carstensen <me@simonbc.com>"]

import glob, zipfile

HEADERS_PATH = '../data/crawl/fec/electronic/headers/'
EFILINGS_PATH = '../data/crawl/fec/electronic/'

def parse_headers():
    """Parse and load the specifications of the FEC electronic filing formats."""

    out = dict()
    for f in glob.glob(HEADERS_PATH + '*.csv'):
        headers = file(f).read().strip().split('\r')
        headers = filter(lambda x: not x.startswith('TEXT'), headers) # remove comments
        ver = f[:-4]
        out[ver] = dict()
        for h in headers:
            cols = [x.strip() for x in h.split(';') if x != '']
            form_type = cols[0].replace(' ', '')
            out[ver][form_type] = cols[1:]
    return out

def value_separator(header):
    """Determine whether the value separator is "," or FS"""
    if header.startswith('/* Header'):
        # we don't know how to parse format verison 2.0
        return None
    comma_separated = header.startswith('HDR,') or header.startswith('"HDR",')
    return comma_separated and ',' or chr(28)

def fixquotes(val):
    """Sometimes values are put inside quotes, remove these"""
    if val.startswith('"') and val.endswith('"'):
        val = val[1:]
        val = val[:-1]
    return val

VERSIONS = ['3.00', '5.00', '5.1', '5.2', '6.1', '6.2']
def get_format_ver(hdr, sep):
    """Determines the format version of a given FEC file"""
    ver = hdr.split(sep)[2]
    ver = fixquotes(ver)
    ver = ver.strip()
    return (ver in VERSIONS and ver) or None

def get_form_type(report, sep, ver):
    ftype = report.split(sep)[0]
    ftype = fixquotes(ftype)
    return ftype

def get_orig_report_id(hdr, sep, ver):
    i = (ver in ['6.1', '6.2'] and 5) or 6
    out = fixquotes(hdr.split(sep)[i])[4:]
    return out

def get_report_no(hdr, sep, ver):
    i = (ver in ['6.1', '6.2'] and 6) or 7
    out = fixquotes(hdr.split(sep)[i])
    return out

SPLIT_RE = re.compile('(,"[^,"]+),([^,"])')
def rsplit(filing, sep):
    """split for FEC records"""
    if sep == ',':
        # make sure we don't split inside quotes
        n = 1
        while n:
            filing, n = SPLIT_RE.subn('\g<1>\x1c\g<2>', filing)
        out = filing.split(',')
        out = [o.replace(chr(28), ',') for o in out]
    else:
        out = filing.split(sep)
        if not out[-1]:
            out = out[:-1]
    out = [fixquotes(o) for o in out]
    return out

def amendment_sort(x, y):
    return cmp(x['report_no'], y['report_no'])

def file_index():
    reports = list()
    amendments = dict()

    files = glob.glob(EFILINGS_PATH + '*.zip')
    files.sort()
    for f in files:
        print >> sys.stderr, '\r', f,
        sys.stderr.flush()

        if not os.stat(f).st_size: continue
        zf = zipfile.ZipFile(f)
        filenames = zf.namelist()
        for fn in filenames:
            d = read_report(f, fn, zf.read(fn))
            if not d: continue
            if d['form_type'].endswith('A'):
                # amendment
                orig_report_id = get_orig_report_id(d['hdr'], d['sep'], d['ver'])
                d['report_no'] = get_report_no(d['hdr'], d['sep'], d['ver'])
                if not amendments.has_key(orig_report_id):
                    amendments[orig_report_id] = list()
                amendments[orig_report_id].append(d)
            else:
                # new report or termination
                reports.append(d)
        zf.close()
    for k, v in amendments.items():
        amendments[k] = sorted(v, amendment_sort)
    return (reports, amendments)

def get_form_id(report, sep):
    return rsplit(report, sep)[1]

def get_committee(report, sep):
    return rsplit(report, sep)[2]

def get_candidate_fec(header, report, form_type, ver):
    if form_type.startswith('F3X'):
        return None
    if ver in ['6.1', '6.2']:
        i = header.index('CANDIDATE ID NUMBER')
    else:
        i = header.index('FEC CANDIDATE ID NUMBER')
    if len(report) <= i: return None
    out = report[i].strip() or None
    return out

def get_contrib_candidate_fec(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('DONOR CANDIDATE FEC ID')
    else:
        i = header.index('FEC CANDIDATE ID NUMBER')
    if len(schedule) <= i: return None
    out = schedule[i] or None
    return out

def get_expend_candidate_fec(header, schedule, ver):
    if ver == '6.1':
        i = header.index('PAYEE CANDIDATE FEC ID')
    elif ver == '6.2':
        i = header.index('BENEFICIARY CANDIDATE FEC ID')
    else:
        i = header.index('FEC CANDIDATE ID NUMBER')
    if len(schedule) <= i: return None
    out = schedule[i] or None
    return out

RE_COMMITTEE = re.compile('([^ ]+ .+) for congress', re.IGNORECASE)
def get_candidate(header, report, form_type, sep, ver):
    fields = rsplit(report, sep)
    if form_type.startswith('F3X'):
        return None
    if ver in ['6.1', '6.2']:
        i_first = header.index('CANDIDATE FIRST NAME')
        i_middle = header.index('CANDIDATE MIDDLE NAME')
        i_last = header.index('CANDIDATE LAST NAME')
        if len(fields) <= i_middle: return None
        middle = fields[i_middle]
        middle = middle + (len(middle) is 1 and '.' or '')
        out = ' '.join(filter(lambda x: x, [fields[i_first], middle, fields[i_last]]))
    else:
        i = header.index('11(d) The Candidate')
        if len(fields) <= i: return None
        out = fields[i]
    if not out:
        #committee name is sometimes 'x for Congress', get candidate name here
        committee = get_committee(report, sep)
        m =  RE_COMMITTEE.match(committee)
        if m:
            out = m.groups()[0]
    return out or None

def get_tran_id(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('TRANSACTION ID NUMBER')
    else:
        i = header.index('TRAN ID')
    if len(schedule) <= i: return None
    out = schedule[i] or None
    return out

def get_occupation(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('CONTRIBUTOR OCCUPATION')
        if len(schedule) <= i: return None
        return schedule[i] or None
    else:
        return None

def get_contributor_org(header, schedule, ver):
    if ver in ['3.00', '5.0']:
        return None
    if ver in ['6.1', '6.2']:
        i = header.index('CONTRIBUTOR ORGANIZATION NAME')
    else:
        i = header.index('CONTRIB ORGANIZATION NAME')

    if len(schedule) <= i: return None
    return schedule[i] or None

def get_contributor(header, sch, ver):
    if ver in ['6.1', '6.2']:
        i_first = header.index('CONTRIBUTOR FIRST NAME')
        i_middle = header.index('CONTRIBUTOR MIDDLE NAME')
        i_last = header.index('CONTRIBUTOR LAST NAME')
        if len(sch) <= i_middle: return None
        middle = sch[i_middle]
        middle = middle + (len(middle) is 1 and '.' or '')
        out = ' '.join(filter(lambda x: x, [sch[i_first], middle, sch[i_last]]))
    else:
        i = header.index('CONTRIBUTOR NAME')
        if len(sch) <= i: return None
        out = sch[i]
    return out or None

def get_employer(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('CONTRIBUTOR EMPLOYER')
        if len(schedule) <= i: return None
        return schedule[i] or None
    else:
        return None

def get_contribution_amount(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('CONTRIBUTION AMOUNT')
    else:
        i = header.index('AMOUNT RECEIVED')
    if len(schedule) <= i: return None
    return schedule[i] or None

def get_expenditure_amount(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('EXPENDITURE AMOUNT')
    else:
        i = header.index('AMOUNT OF EXPENDITURE')
    if len(schedule) <= i: return None
    return schedule[i] or None

def get_recipient(header, sch, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('PAYEE ORGANIZATION NAME')
    else:
        i = header.index('RECIPIENT NAME')
    if len(sch) <= i: return None
    out = sch[i]
    return out.strip() or None

def get_contribution_date(header, sch, ver):
    "YYYYMMDD"
    if ver in ['6.1', '6.2']:
        i = header.index('CONTRIBUTION DATE')
    else:
        i = header.index('DATE RECEIVED')
    if len(sch) <= i: return None
    date = sch[i]
    if not date:
        return None
    year = date[0:4]
    month = date[4:6]
    day = date[6:8]
    return '%s-%s-%s' % (year, month, day)

def get_expenditure_date(header, sch, ver):
    "YYYYMMDD"
    if ver in ['6.1', '6.2']:
        i = header.index('EXPENDITURE DATE')
    else:
        i = header.index('DATE OF EXPENDITURE')
    if len(sch) <= i: return None
    date = sch[i]
    if not date:
        return None
    year = date[0:4]
    month = date[4:6]
    day = date[6:8]
    return '%s-%s-%s' % (year, month, day)

def get_header(headers, form_type, ver):
    if not headers.has_key(ver): return None
    headers = headers[ver]
    if form_type.startswith('F'):
        form_type = form_type[:-1] # remove 'N', 'T' or 'A'
    elif form_type.startswith('S'):
        if ver in ['5.2', '6.1', '6.2']:
            form_type = 'Sch'+form_type[1]
        else:
            form_type = 'S'+form_type[1]
    return headers.has_key(form_type) and headers[form_type] or None

SCH_RE = re.compile('^"?(Sch|S)(A|B)')
SCHA_RE = re.compile('^(Sch|S)A')
def get_schedules(headers, schedules, sep, ver):
    out = dict()
    for s in schedules:
        if not SCH_RE.match(s):
            continue
        sch = dict()
        sch['form_type'] = get_form_type(s, sep, ver)
        header = get_header(headers, sch['form_type'], ver)
        if not header:
            continue
        fields = rsplit(s, sep)
        sch['tran_id'] = get_tran_id(header, fields, ver)
        if SCHA_RE.match(sch['form_type']):
            sch['type'] = 'contribution'
            sch['date'] = get_contribution_date(header, fields, ver)
            sch['contributor_org'] = get_contributor_org(header, fields, ver)
            sch['contributor'] = get_contributor(header, fields, ver)
            sch['occupation'] = get_occupation(header, fields, ver)
            sch['employer'] = get_employer(header, fields, ver)
            sch['amount'] = get_contribution_amount(header, fields, ver)
        else:
            sch['type'] = 'expenditure'
            sch['date'] = get_expenditure_date(header, fields, ver)
            sch['recipient'] = get_recipient(header, fields, ver)
            sch['amount'] = get_expenditure_amount(header, fields, ver)
        out[sch['tran_id']] = sch
    return out

def get_records(data):
    zf = zipfile.ZipFile(EFILINGS_PATH+data['zfn'])
    filing = zf.read(data['report_id']+'.fec')
    lines = filing.split('\n')
    lines = filter(lambda x: x != '', map(lambda x: x.strip(), lines))
    lines = map(lambda x: x.decode('latin1'), lines)
    cover, schedules = lines[1], lines[2:]
    return cover, schedules

def get_report(headers, data):
    cover, schedules = get_records(data)
    form_type, ver, sep = data['form_type'], data['ver'], data['sep']
    header = get_header(headers, form_type, ver)
    out = dict()
    out['filer_id'] = get_form_id(cover, sep)
    out['form_type'] = form_type
    out['report_id'] = data['report_id']
    out['committee'] = get_committee(cover, sep)
    out['candidate'] = get_candidate(header, cover, form_type, sep, ver)
    out['candidate_fec_id'] = get_candidate_fec(header, cover, form_type, ver)
    out['schedules'] = get_schedules(headers, schedules, sep, ver)
    return out

FORM_TYPES = ['F3', 'F3N', 'F3A', 'F3T', 'F3X', 'F3XN', 'F3XA', 'F3T']
def read_report(zfilename, filename, data):
    report_id = filename[:-4]
    lines = data.split('\n')
    lines = filter(lambda x: x != '', map(lambda x: x.strip(), lines))
    lines = map(lambda x: x.decode('latin1'), lines)
    hdr, records = lines[0], lines[1:]
    sep = value_separator(hdr)
    if not sep:
        return None
    ver = get_format_ver(hdr, sep)
    if not ver:
        return None
    form_type = get_form_type(records[0], sep, ver)
    if form_type not in FORM_TYPES:
        return None
    out = dict(zfn=zfilename, report_id=report_id, hdr=hdr, sep=sep, ver=ver, form_type=form_type)
    return out

def apply_amendment(headers, report, amendment):
    cover, schedules = get_records(amendment)
    sep, ver = amendment['sep'], amendment['ver']
    amendment = get_report(headers, amendment)
    report['committee'] = amendment['committee']
    report['candidate'] = amendment['candidate']
    for k, v in amendment['schedules'].items():
        report['schedules'][k] = v

def apply_amendments(headers, report, amendments):
    report_id = report['report_id']
    if amendments.has_key(report_id):
        amendments = amendments[report_id]
        for a in amendments:
            apply_amendment(headers, report, a)
    report['schedules'] = report['schedules'].values()
    return report

def get_filings(headers, reports, amendments):
    for r in reports:
        r = get_report(headers, r)
        r = apply_amendments(headers, r, amendments)
        yield r

def parse_efilings():
    headers = parse_headers()
    reports, amendments = file_index()
    return get_filings(headers, reports, amendments)

if __name__ == "__main__":
    tools.export(parse_efilings())
