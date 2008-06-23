#!/usr/bin/env python
import re
import web
from utils import zip2rep, simplegraphs, apipublish, helpers
import blog
import petition
from settings import db, render
import time
import md5
import urllib, urllib2 

web.config.debug = True
web.template.Template.globals['commify'] = web.commify
web.template.Template.globals['int'] = int
web.template.Template.globals['abs'] = abs
web.template.Template.globals['len'] = len
web.template.Template.globals['query_param'] = helpers.query_param
web.template.Template.globals['changequery'] = web.changequery


options = r'(?:\.(html|xml|rdf|n3|json))'
urls = (
  r'/', 'index',
  r'/us/(?:index%s)?' % options, 'find',
  r'/us/([A-Z][A-Z])', 'redistrict',
  r'/us/([a-z][a-z])%s?' % options, 'state',
  r'/us/([A-Z][A-Z]-\d+)', 'redistrict',
  r'/us/([a-z][a-z]-\d+)%s?' % options, 'district',
  r'/(us|p)/by/(.*)/distribution.png', 'sparkdist',
  r'/(us|p)/by/(.*)', 'dproperty',
  r'/p/(.*?)/introduced', 'politician_introduced',
  r'/p/(.*?)/groups', 'politician_groups',
  r'/p/(.*?)/(\d+)', 'politician_group',
  r'/p/(.*?)%s?' % options, 'politician',
  r'/b/(.*?)%s?' % options, 'bill',
  r'/c', petition.app,
  r'/about(/?)', 'about',
  r'/about/api', 'aboutapi',
  r'/about/feedback', 'feedback',
  r'/blog', blog.app,
  r'/data/(.*)', 'staticdata',
  r'/importcontacts', 'importcontacts',
  r'/bbauth', 'bbauth',
  r'/authsub', 'authsub',
  r'/ydnlIEWXo\.html', 'yauth'
)

class index:
    def GET(self):
        return render.index()

class about:
    def GET(self, endslash=None):
        if not endslash: raise web.seeother('/about/')
        return render.about()

class aboutapi:
    def GET(self):
        return render.about_api()

class feedback:
    def GET(self):
        raise web.seeother('/about')
    
    def POST(self):
        i = web.input(email='info@watchdog.net')
        web.sendmail('Feedback <%s>' % i.email, 'Watchdog <info@watchdog.net>',
          'watchdog.net feedback', 
          i.content +'\n\n' + web.ctx.ip)
        
        return render.feedback_thanks()

class find:
    def GET(self, format=None):
        i = web.input(address=None)
        join = ['district' + ' LEFT OUTER JOIN politician '
                             'ON (politician.district = district.name)']
        pzip5 = re.compile('\d{5}')
        pname = re.compile('[a-zA-Z\.]+')
        pdist = re.compile('[a-zA-Z]{2}\-\d{2}')

        if i.get('zip'):
            if pzip5.match(i.zip):
                try:
                    dists = zip2rep.zip2dist(i.zip, i.address)
                except zip2rep.BadAddress:
                    return render.find_badaddr(i.zip, i.address)
                if len(dists) == 1:
                    raise web.seeother('/us/%s' % dists[0].lower())
                elif len(dists) == 0:
                    return render.find_none(i.zip)
                else:
                    dists = db.select(join, where=web.sqlors('name=', dists))
                    return render.find_multi(i.zip, dists)

            if pdist.match(i.zip):
                raise web.seeother('/us/%s' % i.zip)

            if pname.match(i.zip):
                in_name = i.zip.lower()
                name = in_name.replace(' ', '_')
                vars = {'name':'%%%s%%' % name}
                reps = db.select('politician', where="id like $name", vars=vars)
                if len(reps) == 0:
                    vars = {'name':'%%%s%%' % in_name}
                    reps = db.select('v_politician_name', where="name ilike $name", vars=vars)
                if len(reps) > 1:
                    return render.find_multi_reps(reps)
                else:
                    try:
                        rep = reps[0]
                        web.seeother('/p/%s' % rep.id)
                    except IndexError:
                        raise web.notfound

        else:
            out = apipublish.publish({
              'uri': apipublish.generic(lambda x: 'http://watchdog.net/us/' +
                                        x.name.lower()),
              'type': 'District',
              'name state district voting': apipublish.identity,
              'wikipedia': apipublish.URI,
             }, db.select('district'), format)
            if out is not False:
                return out
            
            dists = db.select(join, order='name asc')
            return render.districtlist(dists)

class state:
    def GET(self, state, format=None):
        state = state.upper()
        try:
            state = db.select('state', where='code=$state', vars=locals())[0]
        except IndexError:
            raise web.notfound
        
        out = apipublish.publish({
          'uri': 'http://watchdog.net/us/' + state.code.lower(),
          'type': 'State',
          'wikipedia': apipublish.URI,
          'code fipscode name status': apipublish.identity,
        }, [state], format)
        if out is not False:
            return out
        
        districts = db.select('district',
                              where='state=$state.code',
                              order='district asc',
                              vars=locals())
        
        return render.state(state, districts.list())

class redistrict:
    def GET(self, district):
        return web.seeother('/us/' + district.lower())

class district:
    def GET(self, district, format=None):
        try:
            district = district.upper()
            d = db.select(['district', 'state', 'politician'],
                          what=('district.*, '
                                'state.name as state_name, '
                                'politician.firstname as pol_firstname, '
                                'politician.lastname as pol_lastname, '
                                'politician.id as pol_id, '
                                'politician.photo_path as pol_photo_path'),
                          where=('district.name = $district AND '
                                 'district.state = state.code AND '
                                 'politician.district = district.name'),
                          vars=locals())[0]
        except IndexError:
            raise web.notfound
        
        out = apipublish.publish({
          'uri': 'http://watchdog.net/us/' + district.lower(),
          'type': 'District',
          'state': apipublish.URI('http://watchdog.net/us/' + d.state.lower()),
          'wikipedia almanac': apipublish.URI,
          'name voting area_sqmi cook_index poverty_pct median_income '
          'est_population est_population_year outline center_lat '
          'center_lng zoom_level': apipublish.identity,
        }, [d], format)
        if out is not False:
            return out
        
        if d.district == 0:
            d.districtth = 'at-large'
        else:
            d.districtth = web.nthstr(d.district)
        
        return render.district(d)

def bills_sponsored(polid):
    "Returns the list of bills sponsored by a politician."
    return db.select('bill', where="sponsor = $polid", vars=locals())

def interest_group_ratings(polid):
    "Returns the interest group ratings for a politician."
    return list(db.select(['interest_group_rating', 'interest_group'],
                          what='year, interest_group.groupname, rating, longname',
                          where=('politician_id = $polid '
                              'AND interest_group.id = interest_group_rating.group_id'),
                          vars=locals()))

def interest_group_table(data):
    "Transform the relational form of the data into something mirroring HTML."
    groupnames = list(set(datum['groupname'] for datum in data))
    groupnames.sort()
    longnames = dict((datum['groupname'], datum['longname']) for datum in data)
    years = list(set(datum['year'] for datum in data))
    years.sort(reverse=True)
    hash = dict(((datum['groupname'], datum['year']), datum['rating'])
                 for datum in data)
    rows = [dict(year=year,
                 ratings=[hash.get((group, year)) for group in groupnames])
            for year in years]
    return dict(groups=[dict(groupname=groupname, longname=longnames[groupname])
                        for groupname in groupnames], rows=rows)

def group_politician_similarity(politician_id, qmin=None):
    """Find the interest groups that vote most like a politician."""
    query_min = lambda mintotal, politician_id=politician_id: db.select(
      'group_politician_similarity'
      ' JOIN interest_group ON (interest_group.id = group_id)', 
      what='*, cast(agreed as float)/total as agreement',
      where='total >= $mintotal AND politician_id=$politician_id ', 
      vars=locals()).list()
    
    if qmin:
        q = query_min(qmin)
    else:
        q = query_min(5)
        if not q:
            q = query_min(3)
            if not q:
                q = query_min(1)
    
    q.sort(lambda x, y: cmp(x.agreement, y.agreement), reverse=True)
    return q 

def interest_group_support(bill_id):
    "Get the support of interest groups for a bill."
    return db.query('select g.longname as longname, sum(gb.support) as support '
             'from  interest_group_bill_support gb , interest_group g '
             'where gb.bill_id = $bill_id and g.id = gb.group_id '
             'group by  gb.bill_id, g.longname '
             'order by sum(gb.support) desc', vars=locals()).list()

def votes_by_party(bill_id):
    "Get the votes of the political parties for a bill"
    result = db.select(['politician p, vote v'],
            what="v.vote, count(v.vote), p.party",
            where="v.politician_id = p.id and v.bill_id = $bill_id "
                    "AND v.vote is not null",
            group="p.party, v.vote",
            vars = locals()
            ).list()
    
    d = {}
    for r in result:
        d.setdefault(r.party, {})
        d[r.party][r.vote] = r.count
    return d

def polname_by_id(pol_id):
    try:
        p = db.select('politician', what='firstname, middlename, lastname', where='id=$pol_id', vars=locals())[0]
    except:
        return None
    else:
        return "%s %s %s" %(p.firstname or '', p.middlename or '', p.lastname or '')
        
def bill_list(format, page=0, limit=50):
    bills = db.select('bill', limit=limit, offset=page*limit, order='session desc').list()
    out = apipublish.publish({
          'uri': apipublish.generic(lambda x: 'http://watchdog.net/b/' + x.id),
          'type': 'Bill',
          'title': apipublish.identity,
         }, bills, format)
    if out:
        return out
    return render.bill_list(bills, limit)

class bill:
    def GET(self, bill_id, format=None):
        if bill_id == "" or bill_id == "index":
            i = web.input(page=0)
            return bill_list(format, int(i.page))
            
        try:
            b = db.select('bill', where='id=$bill_id', vars=locals())[0]
        except IndexError:
            raise web.notfound

        b.sponsorname = polname_by_id(b.sponsor)
        b.interest_group_support = interest_group_support(bill_id)
        b.votes_by_party = votes_by_party(bill_id)
        
        out = apipublish.publish({
          'uri': 'http://watchdog.net/b/' + bill_id,
          'type': 'Bill',
          'session title summary sponsor' : apipublish.identity,
          'interest_group_support': apipublish.table({
                'longname support': apipublish.identity}),
         }, [b], format)
        if out:
            return out
        return render.bill(b)

class politician:
    def GET(self, polid, format=None):
        if polid != polid.lower():
            raise web.seeother('/p/' + polid.lower())
        
        if polid == "" or polid == "index":
            p = db.select(['politician'], order='district asc').list()
            
            out = apipublish.publish({
              'uri': apipublish.generic(lambda x: 'http://watchdog.net/p/' +
                                        x.id),
              'type': 'Politician',
              'district': lambda x: apipublish.URI('http://watchdog.net/us/' +
                                                   x.lower()),
              'wikipedia': apipublish.URI,
             }, p, format)
            if out is not False:
                return out
            
            return render.pollist(p)
        
        try:
            p = db.select(['politician', 'district'],
                          what=("politician.*, "
                                "district.center_lat as d0, "
                                "district.center_lng as d1, "
                                "district.zoom_level as d2"),
                          where=('id=$polid AND '
                                 'district.name = politician.district'),
                          vars=locals())[0]
        except IndexError:
            raise web.notfound

        p.interest_group_rating = interest_group_ratings(polid)
        p.interest_group_table = interest_group_table(p.interest_group_rating)
        p.related_groups = group_politician_similarity(polid)
        p.sponsored_bills = bills_sponsored(polid)                           
            
        out = apipublish.publish({
          'uri': 'http://watchdog.net/p/' + polid,
          'type': 'Politician',
          'district': apipublish.URI('http://watchdog.net/us/' + p.district.lower()),
          'wikipedia photo_credit_url officeurl': apipublish.URI,
          'interest_group_rating': apipublish.table({
                'year groupname longname rating': apipublish.identity}),
          'related_groups' : apipublish.table({
                'longname': apipublish.identity,
                'num_bills_agreed': apipublish.generic(lambda g: g.agreed),
                'num_bills_voted': apipublish.generic(lambda g: g.total),
                'agreement_percent': apipublish.generic(lambda g: int(g.agreement * 100)),
                'group_politician_url': apipublish.generic(lambda g: 
                                        'http://watchdog.net/p/%s/%s' % (polid, g.id))
            }), 
            'sponsored_bills': apipublish.table({
                'id': apipublish.generic(lambda b: '%s. %s' % (b.type.upper(), b.number)),
                'session title introduced': apipublish.identity,
                'url': apipublish.generic(lambda b: 'http://watchdog.net/b/%s' % (b.id))
            }),
          'bioguideid opensecretsid govtrackid gender birthday firstname '
          'middlename lastname party religion photo_path '
          'photo_credit_text '
          'amt_earmark_requested n_earmark_requested n_earmark_received '
          'amt_earmark_received '
          'n_bills_introduced n_bills_enacted n_bills_debated '
          'n_bills_cosponsored '
          'icpsrid nominate predictability '
          'n_speeches words_per_speech': apipublish.identity,
         }, [p], format)
        if out:
            return out
        
        return render.politician(p)

class politician_introduced:
    def GET(self, politician_id):
        sponsored = bills_sponsored(politician_id)
        return render.politician_introduced(sponsored)

class politician_groups:
    def GET(self, politician_id):
        related = group_politician_similarity(politician_id, qmin=1)
        return render.politician_groups(politician_id, related)

class politician_group:
    def GET(self, politician_id, group_id):
        votes = db.select(['vote', 'interest_group_bill_support', 'bill'],
          where="interest_group_bill_support.bill_id = vote.bill_id AND "
                 "vote.bill_id = bill.id AND "
                "politician_id = $politician_id AND group_id = $group_id",
         order='vote = support desc',
          vars=locals())

        return render.politician_group(votes)
        

r_safeproperty = re.compile('^[a-z0-9_]+$')
table_map = {'us': 'district', 'p': 'politician'}

class dproperty:
    def GET(self, table, what):
        try:
            table = table_map[table]
        except KeyError:
            raise web.notfound
        if not r_safeproperty.match(what): raise web.notfound
        
        #if `what` is not there in the `table` (provide available options rather than 404???)
        try:
            maxnum = float(db.select(table,
                                 what='max(%s) as m' % what,
                                 vars=locals())[0].m)
        except:
            raise web.notfound
                                     
        items = db.select(table,
                          what="*, 100*(%s/$maxnum) as pct" % what,
                          order='%s desc' % what,
                          where='%s is not null' % what,
                          vars=locals()).list()
        for item in items:
            if table == 'district':
                item.id = 'd' + item.name
                item.path = '/us/' + item.name.lower()
            elif table == 'politician':
                item.name = '%s %s (%s-%s)' % (item.firstname, item.lastname,
                  item.party[0], item.district.split('-')[0])
                item.path = '/p/' + item.id
        return render.dproperty(items, what)

class sparkdist:
    def GET(self, table, what):
        try:
            table = table_map[table]
        except KeyError:
            raise web.notfound
        if not r_safeproperty.match(what): raise web.notfound
        
        inp = web.input(point=None)
        points = db.select(table, what=what, order=what+' asc', where=what+' is not null')
        points = [x[what] for x in points.list()]
        
        web.header('Content-Type', 'image/png')
        return simplegraphs.sparkline(points, inp.point)

class staticdata:
    def GET(self, path):
        if not web.config.debug:
            raise web.notfound

        assert '..' not in path, 'security'
        return file('data/' + path).read()

class yauth:
    def GET(self):
        return """
Phrase: "# and nation nation moved yet so ship or onwhether so now conceived any the that"
File: "ydnlIEWXo.html"
Url to Check: "http://watchdog.net/ydnlIEWXo.html"
"""


class importcontacts:
    def yahooLoginURL(self, email, url, token=None):
        email = urllib.quote(email)
        lines = open('/home/watchdog/certs/yauth', 'r').readlines()
        appid = lines[0].rstrip()
        secret = lines[1].rstrip()
        ts = time.time()
        appdata = email
        yurl = 'https://api.login.yahoo.com'
        purl = '%s?appid=%s&appdata=%s&ts=%s' % (url,appid, appdata, ts)
        surl ='%s%s' % (purl, secret)
        sig = md5.new(surl).hexdigest()
        furl = '%s%s&sig=%s' % (yurl, purl, sig)
        if token: furl = '%s&token=%s' % ( furl, token)
        return  furl


    def gmailLoginURL(self, email):
        url = 'https://www.google.com/accounts/AuthSubRequest?'
        scope = urllib2.quote('http://www.google.com/m8/feeds/')
        next = urllib2.quote('http://test.pgowda.webfactional.com/authsub')
        url += 'scope='+scope+'&session=1&secure=0&next='+ next
        return url


    def GET(self):
        return render.import_contacts()
    
    def POST(self):
        i = web.input()
        email = i.get('email')
        if 'yahoo' in email:
            ylogin_url = self.yahooLoginURL(email, '/WSLogin/V1/wslogin')
            web.seeother(ylogin_url)

        elif 'google' in email or 'googlemail' in email: 
            glogin_url = self.gmailLoginURL(email)
            web.seeother(glogin_url)
        else:
            return render.import_contacts(message='Not a valid email address. Please try again')


class bbauth:
    def save_contacts(self,email, contacts):
        for c in contacts:
            fields = c['fields']
            cemail = fields[0]['data']
            cfname = ' '; clname = ' '

            if len(fields) > 1:
                cfname = fields[1].get('first', ' ')
                clname = fields[1].get('last', ' ')

            cname = u'%s %s' % (cfname, clname)
            cname = cname.replace('&#39;', ' ').strip()
            vars = {'uemail': email, 'cemail': cemail,
                    'cname': cname, 'provider': 'YAHOO'}
            e = db.select('contacts', where='uemail=$uemail and cemail=$cemail',
                          vars=vars)
            if not e: n = db.insert('contacts', seqname=False, **vars)
            else: db.update('contacts', where='uemail=$uemail and cemail=$cemail',
                            vars=vars, cname=cname)


    def GET(self):
        i = web.input()
        appid = i.get('appid').rstrip()        
        appdata = i.get('appdata')        
        userhash = i.get('userhash')        
        ts = i.get('ts')        
        token = i.get('token')        
        email = session.email        
        #XXX: security verification etc..         
        url = yahooLoginURL(email, '/WSLogin/V1/wspwtoken_login', token)
        resp = urllib2.urlopen(url)        
        content = resp.read()        
        soup = BeautifulSoup(content)        
        aurl = 'http://address.yahooapis.com/v1/searchContacts?format=json'
        wssid = soup.findAll('wssid')[0].contents[0]        
        cookie =soup.findAll('cookie')[0].contents[0]        
        cookie = cookie.strip()        

        for letter in string.uppercase+string.digits:            
            furl = aurl + '&fields=email,name&email.startswith=%s&appid=%s&WSSID=%s' % (letter, appid, wssid)
            req = urllib2.Request(furl)
            req.add_header('Cookie', cookie)
            req.add_header('Content-Type', 'application/json')
            resp = urllib2.urlopen(req).read()
            content = demjson.decode(resp)
            contacts = content.get('contacts')
            if contacts:
                self.save_contacts(email, contacts)
        msg = 'Contacts were imported from your Yahoo address'
        return render.import_contacts(msg)

class authsub:
    def save_contacts(self, uemail,contacts):
        for cemail in contacts:
            cname = ''
            vars = {'uemail': uemail, 'cemail': cemail,
                    'cname':cname, 'provider': 'GMAIL'}
            e = db.select('contacts', where='uemail=$uemail and cemail=$cemail', 
                          vars=vars)
            if not e: n = db.insert('contacts', seqname=False, **vars)
            else: db.update('contacts', where='uemail=$uemail and cemail=$cemail',
                      vars=vars, cname=cname)

    def GET(self):
        i = web.input()
        authToken = i.get('token')
        email = session.mail
        email = quote(email)
        url = ("http://www.google.com/m8/feeds/contacts/%s/full?max-results=999" % email)
        headers = { 'Authorization' : 'AuthSub token="%s"' % authToken.strip() }
        request = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(request)
        tree = ET.XML(response.read())
        items = tree.getiterator()
        contacts = []
        for e in items:
            for i in e:
                #XXX: extract names
                address = i.attrib.get('address')
                if address: emails.append(address)
        
        self.save_contacts(email, contacts)
        msg = 'Contacts were imported from your Gmail Address'
        return render.import_contacts(msg)

app = web.application(urls, globals())
if __name__ == "__main__": app.run()
