#!/usr/bin/env python
import os, re
import web
from utils import zip2rep, simplegraphs, apipublish
import blog

web.config.debug = True
web.template.Template.globals['commify'] = web.commify
web.template.Template.globals['int'] = int
render = web.template.render('templates/', base='base')
db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'),
                  db='watchdog_dev')

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
  r'/p/(.*?)/(\d+)', 'politician_groups',
  r'/p/(.*?)%s?' % options, 'politician',
  r'/b/(.*?)%s?' % options, 'bill',
  r'/about(/?)', 'about',
  r'/about/api', 'aboutapi',
  r'/about/feedback', 'feedback',
  r'/blog', 'reblog',
  r'/blog(/.*)', blog.app,
  r'/data/(.*)', 'staticdata'
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

class reblog:
    def GET(self):
        raise web.seeother('/blog/')

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

def group_politician_similarity(politician_id):
    """Find the interest groups that vote most like a politician."""
    query_min = lambda mintotal, politician_id=politician_id: db.select(
      'group_politician_similarity'
      ' JOIN interest_group ON (interest_group.id = group_id)', 
      what='*, cast(agreed as float)/total as agreement',
      where='total >= $mintotal AND politician_id=$politician_id ', 
      vars=locals()).list()
    
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

class bill:
    def GET(self, bill_id, format=None):
        if bill_id == "" or bill_id == "index":
            bills = db.select(['bill'], order='session desc').list()

            out = apipublish.publish({
              'uri': apipublish.generic(lambda x: 'http://watchdog.net/b/' + x.id),
              'type': 'Bill',
              'title': apipublish.identity,
             }, bills, format)
            if out:
                return out
            return render.bill_list(bills)

        try:
            b = db.select('bill', where='id=$bill_id', vars=locals())[0]
        except IndexError:
            raise web.notfound

        b.interest_group_support = interest_group_support(bill_id)
        
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
        p.related_groups = group_politician_similarity(polid) #@@ API
        p.sponsored_bills = bills_sponsored(polid) #@@ API

        out = apipublish.publish({
          'uri': 'http://watchdog.net/p/' + polid,
          'type': 'Politician',
          'district': apipublish.URI('http://watchdog.net/us/' + p.district.lower()),
          'wikipedia photo_credit_url officeurl': apipublish.URI,
          'interest_group_rating': apipublish.table({
            'year groupname longname rating': apipublish.identity}),
          'bioguideid opensecretsid govtrackid gender birthday firstname '
          'middlename lastname party religion photo_path '
          'photo_credit_text '
          ' amt_earmark_requested n_earmark_requested n_earmark_received '
          'amt_earmark_received '
          'n_speeches words_per_speech': apipublish.identity,
         }, [p], format)
        if out is not False:
            return out
        
        return render.politician(p)

class politician_groups:
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
        
        maxnum = float(db.select(table,
                                 what='max(%s) as m' % what,
                                 vars=locals())[0].m)
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
                item.name = item.firstname + ' ' + item.lastname
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

app = web.application(urls, globals())
if __name__ == "__main__": app.run()
