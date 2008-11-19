import simplejson as json
import web
import smartersql as sql

from settings import db
sql.Table.db = db

class State(sql.Table):
    @property
    def _uri_(self):
        return 'http://watchdog.net/us/%s#it' % self.code.lower()
    
    # states.json
    code = sql.String(2, primary=True)
    name = sql.String(256)
    status = sql.String(256)
    wikipedia = sql.URL()
    fipscode = sql.String(2)
    
    senators = sql.Backreference('Politician', 'district')
    districts = sql.Backreference('District', 'state', order='name asc')

class District(sql.Table):
    @property
    def _uri_(self):
        return 'http://watchdog.net/us/%s#it' % self.name.lower()
    
    # districts.json
    name = sql.String(10, primary=True)
    district = sql.Integer()
    state = sql.Reference(State) #@@renames to state_id
    voting = sql.Boolean()
    wikipedia = sql.URL()
    
    politician = sql.Backreference('Politician', 'district')
    
    @property
    def districtth(self):
        if self.district == 0:
            return 'at-large'
        else:
            return web.nthstr(self.district)

    # almanac.json
    almanac = sql.URL()
    area_sqmi = sql.Number() #@@Square Miles
    cook_index = sql.String() #@@integer
    poverty_pct = sql.Percentage()
    median_income = sql.Dollars()
    est_population = sql.Number()      # most recent population estimate
    est_population_year = sql.Year()   # year of the estimate
    
    # shapes.json
    outline = sql.String(export=False) #@@geojson
    
    # centers.json
    center_lat = sql.Float() #@@ latlong type
    center_lng = sql.Float()
    zoom_level = sql.Integer()

    earmark_per_capita = sql.Float()

class Zip(sql.Table):
    zip = sql.String(5, primary=True)
    city = sql.String()
    state = sql.String(2) #@@ reference state...(@@no AE=Armed Forces Europe)
    gini = sql.Float()
    # @@other IRS stuff

class Zip4(sql.Table):
    zip = sql.String(5, primary=True) #@@references zip, (seems some ZIP+4s aren't in ctyst?)
    plus4 = sql.String(4, primary=True)
    district = sql.Reference(District)

#--alter table zip4 drop constraint zip4_pkey;
#--COPY zip4 FROM  '/home/watchdog/web/data/load/zip4.tsv';
#alter table zip4 add primary key (zip, plus4);
#--alter table zip4 add constraint "zip4_district_fkey" FOREIGN KEY (district) REFERENCES district(name) #@@
#--GRANT ALL ON zip4 TO watchdog;

class GovtrackID(sql.URL):
    towhatever = lambda f: (lambda self, x, *a: f(self, 
      'http://www.govtrack.us/congress/person.xpd?id=' + x, *a))
    toxml = towhatever(sql.URL.toxml)
    ton3 = towhatever(sql.URL.ton3)

class Politician(sql.Table):
    @property
    def _uri_(self): return 'http://watchdog.net/p/%s#it' % self.id
    
    # politicians.json
    id = sql.String(256, primary=True)
    district = sql.Reference(District) #@@ renames to district_id
    wikipedia = sql.URL()
  
    # govtrack.json --@@get from votesmart?
    bioguideid = sql.String()
    opensecretsid = sql.String()
    govtrackid = GovtrackID()
    gender = sql.String(1)
    birthday = sql.String() #@@date
    firstname = sql.String()
    middlename = sql.String()
    lastname = sql.String()
    
    def xmllines(self):
        sameas = lambda x: '  <owl:sameAs xmlns:owl="http://www.w3.org/2002/07/owl#" \
rdf:resource="%s" />' % x
        return [sameas(x) for x in self.akas()]
    
    def n3lines(self, indent):
        sameas = lambda x: indent + '<http://www.w3.org/2002/07/owl#sameAs> <%s>;' % x
        return [sameas(x) for x in self.akas()]
    
    def akas(self):
        if self.bioguideid:
            yield 'http://www.rdfabout.com/rdf/usgov/congress/people/' + self.bioguideid
        if self.wikipedia:
            yield 'http://dbpedia.org/resource/' + self.wikipedia.split('/')[-1]
    
    @property
    def name(self):
        if hasattr(self, 'nickname') and self.nickname:
            return self.nickname + ' ' + self.lastname
        else:
            return self.fullname
    
    @property
    def fullname(self):
        return (self.firstname or '') + ' ' + (self.middlename or '') + ' ' + (self.lastname or '')
    
    @property
    def title(self):
        dist = self.district_id
        return 'Sen.' if State.where(code=dist) else 'Rep.'
    
    officeurl = sql.URL()
    party = sql.String()
    religion = sql.String()
    
    n_bills_introduced = sql.Number()
    n_bills_enacted = sql.Number()
    n_bills_debated = sql.Number()
    n_bills_cosponsored = sql.Number()
    n_speeches = sql.Number()
    words_per_speech = sql.Number()
  
    # voteview.json
    icpsrid = sql.Integer()
    nominate = sql.Float() #@@
    predictability = sql.Percentage()
  
    # earmarks.json
    amt_earmark_requested = sql.Dollars(default=0)
    n_earmark_requested = sql.Number(default=0)
    n_earmark_received = sql.Number(default=0)
    amt_earmark_received = sql.Dollars(default=0)
    
    # photos.json
    photo_path = sql.URL()
    photo_credit_url = sql.URL()
    photo_credit_text = sql.String()
  
    # fec
    money_raised = sql.Dollars()
    pct_spent = sql.Percentage()
    pct_self = sql.Percentage()
    pct_indiv = sql.Percentage()
    pct_pac = sql.Percentage()
  
    # votesmart
    nickname = sql.String()
    votesmartid = sql.String()
    birthplace = sql.String()
    education = sql.String()
  
    # punch
    chips2008 = sql.Percentage()
    progressive2008 = sql.Percentage()
    progressiveall = sql.Percentage()
  
    # opensecrets
    pct_pac_business = sql.Percentage()
    
    # almanac.json
    n_vote_received = sql.Number()
    pct_vote_received = sql.Percentage()
    last_elected_year = sql.Number()

    bills_sponsored = sql.Backreference('Bill', 'sponsor')
    earmarks_sponsored = sql.Backreference('Earmark_sponsor', 'politician')

class Politician_FEC_IDs(sql.Table):
    politician = sql.Reference(Politician, primary=True)
    fec_id = sql.String(primary=True)
    # cycle = sql.Integer()

class Interest_Group(sql.Table): # @@capitalization looks dorky..
    id = sql.Serial(primary=True)
    groupname = sql.String(10)
    category_id = sql.String(10) # references category,
    longname  = sql.String(unique=True)

class Interest_group_rating(sql.Table):
    """interest group scores for politicians"""
    politician = sql.Reference(Politician)

    # almanac.json
    year = sql.Year()
    group = sql.Reference(Interest_Group)
    rating = sql.Integer() # typically 0-100

class Bill(sql.Table):
    @property
    def _uri_(self):
        return 'http://watchdog.net/b/%s#it' % self.id
    
    id = sql.String(primary=True)
    session = sql.Integer()
    type = sql.String(5)
    number = sql.Integer()
    introduced = sql.Date()
    title = sql.String()
    sponsor = sql.Reference(Politician) #@@rename to sponsor_id
    summary = sql.String()
    maplightid = sql.String(10)
    
    interest_group_support = sql.Backreference('Interest_group_bill_support', 'bill', order='support desc')
    
    @property
    def name(self):
        typemap = {
          'h': 'H.R.', 
          's': 'S.', 
          'hj': 'H.J.Res.', 
          'sj': 'S.J.Res.',
          'hc': 'H.Con.Res.',
          'sc': 'S.Con.Res.',
          'hr': 'H.Res.',
          'sr': 'S.Res.'
        }
        
        return typemap[self.type] + ' ' + str(self.number)
    
    @property
    def votes_by_party(self):
        """Get the votes of the political parties for a bill."""
        result = db.select(['politician p, position v'],
                what="v.vote, count(v.vote), p.party",
                where="v.politician_id = p.id and v.bill_id = $self.id "
                        "AND v.vote is not null",
                group="p.party, v.vote",
                vars = locals()
                ).list()

        d = {}
        for r in result:
            d.setdefault(r.party, {})
            d[r.party][r.vote] = r.count
        return d
    
    @property
    def votes_by_caucus(self):
        caucuses = json.load(file('import/load/manual/caucuses.json'))
        members = sum([x['members'] for x in caucuses], [])
        result = db.select(['position'],
            where=web.sqlors('politician_id=', members) + 
              'AND bill_id=' + web.sqlquote(self.id),
            vars=locals()
            ).list()
        
        if not result: return None
        
        votemap = dict((r.politician_id, r.vote) for r in result)
        d = {}
        for c in caucuses:
            cdict = d[c['name']] = {}
            for m in c['members']:
                v = votemap.get(m)
                cdict.setdefault(v, 0)
                cdict[v] += 1
        return d

class Roll(sql.Table):
    id = sql.String(primary=True)
    type = sql.String()
    question = sql.String()
    required = sql.String()
    result = sql.String()
    bill = sql.Reference(Bill)
    
    #@@@@@ DON'T REPEAT YOURSELF
    @property
    def votes_by_party(self):
        """Get the votes of the political parties for a bill."""
        result = db.select(['politician p, vote v'],
                what="v.vote, count(v.vote), p.party",
                where="v.politician_id = p.id and v.roll_id = $self.id "
                        "AND v.vote is not null",
                group="p.party, v.vote",
                vars = locals()
                ).list()

        d = {}
        for r in result:
            d.setdefault(r.party, {})
            d[r.party][r.vote] = r.count
        return d
    
    @property
    def votes_by_caucus(self):
        caucuses = json.load(file('import/load/manual/caucuses.json'))
        members = sum([x['members'] for x in caucuses], [])
        result = db.select(['vote'],
            where=web.sqlors('politician_id=', members) + 
              'AND roll_id=' + web.sqlquote(self.id),
            vars=locals()
            ).list()
        
        if not result: return None
        
        votemap = dict((r.politician_id, r.vote) for r in result)
        d = {}
        for c in caucuses:
            cdict = d[c['name']] = {}
            for m in c['members']:
                v = votemap.get(m)
                cdict.setdefault(v, 0)
                cdict[v] += 1
        return d

class Vote(sql.Table):
    roll = sql.Reference(Roll, primary=True)
    politician = sql.Reference(Politician, primary=True)
    vote = sql.Int2()

class Position(sql.Table):
    bill = sql.Reference(Bill, primary=True)
    politician = sql.Reference(Politician, primary=True)
    vote = sql.Int2()

class Interest_group_bill_support(sql.Table):
    bill = sql.Reference(Bill, primary=True)
    group = sql.Reference(Interest_Group, primary=True)
    support = sql.Int2()

class Group_politician_similarity(sql.Table):
    group = sql.Reference(Interest_Group, primary=True)
    politician = sql.Reference(Politician, primary=True)
    agreed = sql.Integer()
    total = sql.Integer()

class Category (sql.Table):
    id = sql.String(10, primary=True)
    name = sql.String()
    industry = sql.String()
    sector = sql.String()

class Contribution (sql.Table):
    id = sql.Serial(primary=True)
    politician_id = sql.Reference(Politician)
    committee = sql.String()
    contrib_date = sql.Date()
    contributor_org = sql.String()
    contributor = sql.String()
    occupation = sql.String()
    employer = sql.String()
    employer_stem = sql.String()
    candidate_name = sql.String()
    filer_id = sql.String(10)
    report_id = sql.Integer()
    amount = sql.String(20)

#@@INDEX by employer_stem

class Earmark(sql.Table):
    id = sql.Integer(primary=True)
    house_request = sql.Dollars()
    senate_request = sql.Dollars()
    final_amt = sql.Dollars()
    budget_request = sql.Dollars()
    prereduction_amt = sql.Dollars()
    description = sql.String()
    city = sql.String() # eventually a ref, we hope
    county = sql.String()
    state = sql.String() #@@ref?
    bill = sql.String() #@@ref
    bill_section = sql.String()
    bill_subsection = sql.String()
    project_heading = sql.String()
    district = sql.Integer()
    presidential = sql.String()
    undisclosed = sql.String()
    intended_recipient = sql.String()
    recipient_stem = sql.String()
    notes = sql.String()    
    sponsors = sql.Backreference('Earmark_sponsor', 'earmark')

class Earmark_sponsor(sql.Table):
    earmark = sql.Reference(Earmark, primary=True)
    politician = sql.Reference(Politician, primary=True)


## Lobbyiest stuff:
class lob_organization(sql.Table):
    id = sql.Number(primary=True)  #@@TODO: design stable ids
    name = sql.String()
    filings = sql.Backreference('lob_filing', 'org')

class lob_person(sql.Table):
    id = sql.Number(primary=True)  #@@TODO: design stable ids
    prefix = sql.String()
    firstname = sql.String()
    middlename = sql.String()
    lastname = sql.String()
    suffix = sql.String()
    contact_name = sql.String()
    filings = sql.Backreference('lob_filing', 'lobbyist')

class lob_pac(sql.Table):
    id = sql.Number(primary=True)  #@@TODO: design stable ids
    name = sql.String()
    filings = sql.Backreference('lob_pac_filings', 'pac')

class lob_filing(sql.Table):
    id = sql.Number(primary=True)  #Uses xml file number as a stable id.
    year = sql.Year()
    type = sql.String()
    signed_date = sql.Date()
    amendment = sql.Boolean()
    certified = sql.Boolean()
    comments = sql.String()

    senate_id = sql.Number()
    house_id = sql.Number()
    filer_type = sql.String(1)

    lobbyist = sql.Reference(lob_person)
    org = sql.Reference(lob_organization)
    pacs = sql.Backreference('lob_pac_filings', 'filing')
    contributions = sql.Backreference('lob_contribution', 'filing', order='amount asc')
    @property
    def house_url(self):
        return "http://disclosures.house.gov/lc/xmlform.aspx?id=%d" % self.id

class lob_contribution(sql.Table):
    filing = sql.Reference(lob_filing)
    date = sql.Date()
    type = sql.String()
    contributor = sql.String()
    payee = sql.String()
    recipient = sql.String()
    amount = sql.Dollars()
    politician = sql.Reference(Politician)

class lob_pac_filings(sql.Table):
    pac = sql.Reference(lob_pac)
    filing = sql.Reference(lob_filing)


class Expenditure (sql.Table):
    id = sql.Serial(primary=True)
    candidate_name = sql.String()
    committee = sql.String()
    expenditure_date = sql.Date()
    recipient = sql.String()
    filer_id = sql.String(10)
    report_id = sql.Integer()
    amount = sql.String(20)

class SOI(sql.Table):
    #district_id = sql.String(10, primary=True) 
    district = sql.Reference(District, primary=True)
    # irs/soi
    bracket_low = sql.Integer(primary=True)
    agi = sql.Float()
    n_dependents = sql.Float()
    n_eitc = sql.Float()
    n_filers = sql.Float()
    n_prepared = sql.Float()
    tot_charity = sql.Float()
    tot_eitc = sql.Float()
    tot_tax = sql.Float()
    avg_dependents = sql.Float()
    avg_eitc = sql.Float()
    avg_income = sql.Float()
    avg_taxburden = sql.Float()
    pct_charity = sql.Percentage()
    pct_eitc = sql.Percentage()
    pct_prepared = sql.Percentage()

class Census_meta(sql.Table):
    internal_key = sql.String(10, primary=True)
    census_type = sql.Integer(primary=True)
    hr_key = sql.String(512)
    label = sql.String()

class Census_data(sql.Table):
    #district_id = sql.String(10, primary=True) 
    district = sql.Reference(District, primary=True)
    internal_key = sql.String(10, primary=True)
    census_type = sql.Integer(primary=True)
    value = sql.Float()

class Pol_contacts(sql.Table):
    politician = sql.Reference(Politician, primary=True)
    contact = sql.String()
    contacttype = sql.String(1)     # E=email, W=wyr, I=ima, Z=zipauth
    captcha = sql.Boolean()

class Census_Population(sql.Table):
    state_id = sql.String(2)     # STATE
    county_id = sql.String(3)    # COUNTY
    blockgrp_id = sql.String(1)  # BLOCKGRP
    block_id = sql.String(4)     # BLOCK
    district_id = sql.String(2)  # CD110
    tract_id = sql.String(6)     # TRACT
    zip_id = sql.String(5)       # ZCTA
    sumlev = sql.String(16)      # SUMLEV
    area_land = sql.Integer()    # AREALAND
    area_land.sql_type = 'bigint'
    population = sql.Integer()   

def init():
    db.query("CREATE VIEW census AS select * from census_meta NATURAL JOIN census_data")
    try:
        db.query("GRANT ALL on census TO watchdog")
    except:
        pass # group doesn't exist

