#!/usr/bin/env python
import re, sys
import web
web.config.debug = True

from utils import zip2rep, simplegraphs, apipublish, users, writerep
import blog
import petition
import settings
from settings import db, render
import schema

options = r'(?:\.(html|xml|rdf|n3|json))'
urls = (
  r'/', 'index',
  r'/us/(?:index%s)?' % options, 'find',
  r'/us/([A-Z][A-Z])', 'redistrict',
  r'/us/([a-z][a-z])%s?' % options, 'state',
  r'/us/([A-Z][A-Z]-\d+)', 'redistrict',
  r'/us/([a-z][a-z]-\d+)%s?' % options, 'district',
  r'/(us|p)/by/(.*)/distribution\.png', 'sparkdist',
  r'/(us|p)/by/(.*)', 'dproperty',
  r'/p/(.*?)/introduced', 'politician_introduced',
  r'/p/(.*?)/groups', 'politician_groups',
  r'/p/(.*?)/(\d+)', 'politician_group',
  r'/p/(.*?)%s?' % options, 'politician',
  r'/e/(.*?)%s?' % options, 'earmark',
  r'/b/(.*?)%s?' % options, 'bill',
  r'/r/us/(.*?)%s?' % options, 'roll',
  r'/c', petition.app,
  r'/u', users.app,
  r'/writerep', writerep.app,
  r'/about(/?)', 'about',
  r'/about/api', 'aboutapi',
  r'/about/feedback', 'feedback',
  r'/blog', blog.app,
  r'/data/(.*)', 'staticdata',
  r'/bbauth/', 'contacts.auth_yahoo',
  r'/authsub', 'contacts.auth_google',
  r'/auth/msn', 'contacts.auth_msn',
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
        pzip5 = re.compile(r'\d{5}')
        pzip4 = re.compile(r'\d{5}-\d{4}')
        pname = re.compile(r'[a-zA-Z\.]+')
        pdist = re.compile(r'[a-zA-Z]{2}\-\d{2}')
        
        dists = None
        if i.get('zip'):
            if pzip4.match(i.zip):
                zip, plus4 = i.zip.split('-')
                dists = [x.district for x in
                  db.select('zip4', where='zip=$zip and plus4=$plus4', vars=locals())]
            
            elif pzip5.match(i.zip):
                try:
                    dists = zip2rep.zip2dist(i.zip, i.address)
                except zip2rep.BadAddress:
                    return render.find_badaddr(i.zip, i.address)
            
            if dists:
                d_dists = schema.District.select(where=web.sqlors('name=', dists))
                out = apipublish.publish(d_dists, format)
                if out: return out

                if len(dists) == 1:
                    raise web.seeother('/us/%s' % dists[0].lower())
                elif len(dists) == 0:
                    return render.find_none(i.zip)
                else:
                    return render.find_multi(i.zip, d_dists)

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
            index = schema.District.select(order='name asc')
            out = apipublish.publish(index, format)
            if out: return out

            return render.districtlist(index)

class state:
    def GET(self, state, format=None):
        try:
            state = schema.State.where(code=state.upper())[0]
        except IndexError:
            raise web.notfound

        out = apipublish.publish([state], format)
        if out: return out

        return render.state(state)

class redistrict:
    def GET(self, district):
        return web.seeother('/us/' + district.lower())

class district:
    def GET(self, district, format=None):
        try:
            d = schema.District.where(name=district.upper())[0]
        except IndexError:
            raise web.notfound
        
        out = apipublish.publish([d], format)
        if out: return out
        
        pos = web.storage()
        spark_keys = ['area_sqmi', 'est_population', 'poverty_pct', 'median_income']
        for k in spark_keys:
            pos[k] = sparkpos('district', k, district)
            print >>sys.stderr, "Position of %s on %s is %d" %( district, k, pos[k])

        return render.district(d, pos)

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

def bill_list(format, page=0, limit=50):
    bills = schema.Bill.select(limit=limit, offset=page*limit, order='session desc, introduced desc, number desc')

    out = apipublish.publish(bills, format)
    if out: return out
    #@@ add link to next page

    return render.bill_list(bills, limit)

class roll:
    def GET(self, roll_id, format=None):
        try:
            b = schema.Roll.where(id=roll_id)[0]
            votes = schema.Vote.where(roll_id=b.id)
        except IndexError:
            raise web.notfound

        out = apipublish.publish([b], format)
        if out: return out
        
        def votepct(pvotes):
            s = (float(pvotes.get(1, 0)) / sum(pvotes.values()))
            return str(s * 100)[:4].rstrip('.') + '%'

        return render.roll(b, votes, votepct)

class bill:
    def GET(self, bill_id, format=None):
        if bill_id == "" or bill_id == "index":
            i = web.input(page=0)
            return bill_list(format, int(i.page))
        
        try:
            b = schema.Bill.where(id=bill_id)[0]
        except IndexError:
            raise web.notfound
        
        out = apipublish.publish([b], format)
        if out: return out
        
        return render.bill(b)

def earmark_list(format, page=0, limit=50):
    earmarks = schema.Earmark.select(limit=limit, offset=page*limit, order='id')

    out = apipublish.publish(earmarks, format)
    if out: return out
    return render.earmark_list(earmarks, limit)
def earmark_pol_list(pol_id, format, page=0, limit=50):
    p = schema.Politician.where(id=pol_id)[0].earmarks_sponsored
    if p:
        earmarks = map(lambda x: x.earmark, p)
    else: 
        # @@TODO: something better here. 
        raise web.notfound
    out = apipublish.publish(earmarks, format)
    if out: return out
    return render.earmark_list(earmarks, limit)

class earmark:
    def GET(self, earmark_id, format=None):
        # No earmark id, show list
        if earmark_id == "" or earmark_id == "index":
            # Show earmark list
            i = web.input(page=0)
            return earmark_list(format, int(i.page))
        em = None
        # Check if we were given a politician_id
        try:
            em = schema.Politician.where(id=earmark_id)[0]
        except IndexError:
            pass # not found
        if em:
            return earmark_pol_list(earmark_id, format)
        # Display the specific earmark
        try:
            em = schema.Earmark.where(id=int(earmark_id))[0]
        except IndexError:
            raise web.notfound
        except ValueError:
            raise web.notfound
        return render.earmark(em)


class politician:
    def GET(self, polid, format=None):
        if polid != polid.lower():
            raise web.seeother('/p/' + polid.lower())
        
        i = web.input()
        idlookup = False
        for k in ['votesmartid', 'bioguideid', 'opensecretsid', 'govtrackid']:
            if i.get(k):
                idlookup = True
                ps = schema.Politician.where(**{k: i[k]})
                if ps: raise web.seeother('/p/' + ps[0].id)

        if idlookup:
            # we were looking up by ID but nothing matched
            raise web.notfound

        if polid == "" or polid == "index":
            p = schema.Politician.select(order='district_id asc')

            out = apipublish.publish(p, format)
            if out: return out

            return render.pollist(p)

        try:
            p = schema.Politician.where(id=polid)[0]
        except IndexError:
            raise web.notfound

        #@@move into schema
        p.fec_ids = [x.fec_id for x in db.select('politician_fec_ids', what='fec_id',
          where='politician_id=$polid', vars=locals())]

        p.related_groups = group_politician_similarity(polid)

        out = apipublish.publish([p], format)
        if out: return out

        pos = web.storage()
        spark_keys = ['money_raised', 'pct_spent', 'pct_self', 'pct_indiv',
                'pct_pac', 'n_earmark_requested', 'amt_earmark_requested',
                'n_earmark_received', 'amt_earmark_received',
                'n_bills_cosponsored', 'n_bills_introduced', 'n_bills_debated',
                'n_bills_enacted', 'n_speeches', 'words_per_speech',
                'nominate', 'predictability']
        for k in spark_keys:
            pos[k] = sparkpos('politician',k,polid)

        return render.politician(p, pos)

class politician_introduced:
    def GET(self, politician_id):
        pol = schema.Politician.where(id=politician_id)[0]
        return render.politician_introduced(pol)

class politician_groups:
    def GET(self, politician_id):
        related = group_politician_similarity(politician_id, qmin=1)
        return render.politician_groups(politician_id, related)

class politician_group:
    def GET(self, politician_id, group_id):
        votes = db.select(['position', 'interest_group_bill_support', 'bill'],
          where="interest_group_bill_support.bill_id = position.bill_id AND "
                 "position.bill_id = bill.id AND "
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
                  (item.party or 'I')[0], item.district_id.split('-')[0])
                item.path = '/p/' + item.id
        return render.dproperty(items, what)

def sparkpos(table, what, id):
    if table == 'district':
        id_col = 'name'
        id = id.upper()
    elif table == 'politician':
        id_col= 'id'
    else: return 0
    # @@TODO: make sure this is injection safe.
    item = db.query("select count(*) as position from %(table)s, (select * from %(table)s where %(id_col)s='%(who)s') as a where %(table)s.%(what)s > a.%(what)s" %  {'table':table, 'what':what, 'who':id, 'id_col':id_col})[0]
    return item.position + 1 # '#1' looks better than '#0'

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
settings.setup_session(app)

if __name__ == "__main__": app.run()
