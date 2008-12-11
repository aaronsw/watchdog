#!/usr/bin/env python
import re, sys
import web

from utils import zip2rep, simplegraphs, apipublish, users, writerep, se, wyrapp
import blog
import petition
import settings
from settings import db, render, production_mode
import schema
import config

if not production_mode:
	web.config.debug = True

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
  r'/p/(.*?)/lobby', 'politician_lobby',
  r'/p/(.*?)/earmarks', 'politician_earmarks',
  r'/p/(.*?)/introduced', 'politician_introduced',
  r'/p/(.*?)/groups', 'politician_groups',
  r'/p/(.*?)/(\d+)', 'politician_group',
  r'/p/(.*?)%s?' % options, 'politician',
  r'/e/(.*?)%s?' % options, 'earmark',
  r'/b/(.*?)%s?' % options, 'bill',
  r'/r/us/(.*?)%s?' % options, 'roll',
  r'/c', petition.app,
  r'/u', users.app,
  r'/l/c/?(.*?)', 'lob_contrib',
  r'/l/f/?(.*?)', 'lob_filing',
  r'/l/o/?(.*?)', 'lob_org',
  r'/l/pa/?(.*?)', 'lob_pac',
  r'/l/pe/?(.*?)', 'lob_person',
  r'/writerep', wyrapp.app,
  r'/about(/?)', 'about',
  r'/about/team', 'aboutteam',
  r'/about/help', 'abouthelp',
  r'/about/api', 'aboutapi',
  r'/about/feedback', 'feedback',
  r'/blog', blog.app,
  r'/share', 'petition.share',
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

class aboutteam:
    def GET(self):
        return render.about_team()

class abouthelp:
    def GET(self):
        return render.about_help()

class feedback:
    def GET(self):
        return render.feedback()

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
        pdist = re.compile(r'[a-zA-Z]{2}\-\d{2}')
        
        dists = None
        if not i.get('q'):
            i.q = i.get('zip')
        
        if i.q:
            if pzip4.match(i.q):
                zip, plus4 = i.q.split('-')
                dists = [x.district for x in
                  db.select('zip4', where='zip=$zip and plus4=$plus4', vars=locals())]
            
            elif pzip5.match(i.q):
                try:
                    dists = zip2rep.zip2dist(i.q, i.address)
                except zip2rep.BadAddress:
                    return render.find_badaddr(i.q, i.address)
            
            if dists:
                d_dists = schema.District.select(where=web.sqlors('name=', dists))
                out = apipublish.publish(d_dists, format)
                if out: return out

                if len(dists) == 1:
                    raise web.seeother('/us/%s' % dists[0].lower())
                elif len(dists) == 0:
                    return render.find_none(i.q)
                else:
                    return render.find_multi(i.q, d_dists)

            if pdist.match(i.q):
                raise web.seeother('/us/%s' % i.q)
            
            results = se.query(i.q)
            reps = db.select('politician', where=web.sqlors('id=', results))
            if len(reps) > 1:
                return render.find_multi_reps(reps)
            else:
                try:
                    rep = reps[0]
                    web.seeother('/p/%s' % rep.id)
                except IndexError:
                    raise web.notfound()

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
            raise web.notfound()

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
            raise web.notfound()
        
        out = apipublish.publish([d], format)
        if out: return out
        
        return render.district(d, sparkpos)

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
            raise web.notfound()

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
            raise web.notfound()
        
        out = apipublish.publish([b], format)
        if out: return out
        
        return render.bill(b)

def earmark_list(format, page=0, limit=50):
    earmarks = schema.Earmark.select(limit=limit, offset=page*limit, order='id')

    out = apipublish.publish(earmarks, format)
    if out: return out
    return render.earmark_list(earmarks, limit)
def earmark_pol_list(pol_id, format, page=0, limit=50):
    earmarks = db.select(['earmark_sponsor', 'earmark'], what='earmark.*', 
            where='politician_id = $pol_id AND earmark_id=earmark.id', 
            order='final_amt desc', vars=locals())
    if not earmarks:
        # @@TODO: something better here. 
        raise web.notfound()
    out = apipublish.publish(earmarks, format)
    if out: return out
    return render.earmark_list(earmarks, limit)

class politician_earmarks:
    def GET(self, polid, format=None):
        try:
            em = schema.Politician.where(id=polid)[0]
        except IndexError:
            raise web.notfound()
        return earmark_pol_list(polid, format)
class earmark:
    def GET(self, earmark_id, format=None):
        # No earmark id, show list
        if earmark_id == "" or earmark_id == "index":
            # Show earmark list
            i = web.input(page=0)
            return earmark_list(format, int(i.page))
        # Display the specific earmark
        try:
            em = schema.Earmark.where(id=int(earmark_id))[0]
        except IndexError:
            raise web.notfound()
        except ValueError:
            raise web.notfound()
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
            raise web.notfound()

        if polid == "" or polid == "index":
            p = schema.Politician.select(order='district_id asc')

            out = apipublish.publish(p, format)
            if out: return out

            return render.pollist(p)

        try:
            p = schema.Politician.where(id=polid)[0]
        except IndexError:
            raise web.notfound()

        #@@move into schema
        p.fec_ids = [x.fec_id for x in db.select('politician_fec_ids', what='fec_id',
          where='politician_id=$polid', vars=locals())]

        p.related_groups = group_politician_similarity(polid)
        out = apipublish.publish([p], format)
        if out: return out

        return render.politician(p, sparkpos)

class politician_lobby:
    def GET(self, polid, format=None):
        limit = 50
        page = int(web.input(page=0).page)
        #c = schema.lob_contribution.select(where='politician_id=$polid', limit=limit, offset=page*limit, order='amount desc', vars=locals())
        a = db.select(['lob_filing', 'lob_contribution'], 
                what='SUM(amount)',
                where="politician_id = $polid AND lob_filing.id = filing_id",
                vars=locals())[0].sum
        c = db.select(['lob_organization', 'lob_filing', 'lob_contribution', 'lob_person'], 
                where="politician_id = $polid and lob_filing.id = filing_id and lob_organization.id = org_id and lob_person.id = lobbyist_id", 
                order='amount desc', limit=limit, offset=page*limit,
                vars=locals())
        return render.politician_lobby(c, a, limit)
class lob_filing:
    def GET(self, filing_id):
        limit = 50
        page = int(web.input(page=0).page)
        if filing_id:
            f = schema.lob_filing.select(where='id=$filing_id', limit=limit, offset=page*limit, vars=locals())
        else:
            f = schema.lob_filing.select(limit=limit, offset=page*limit)
        return render.lob_filings(f,limit)
class lob_contrib:
    def GET(self, filing_id):
        limit = 50
        page = int(web.input(page=0).page)
        if filing_id:
            c = schema.lob_contribution.select(where='filing_id=$filing_id', limit=limit, offset=page*limit, order='amount desc', vars=locals())
        else:
            c = schema.lob_contribution.select(limit=limit, offset=page*limit, order='amount desc')
        return render.lob_contributions(c, limit)
class lob_pac:
    def GET(self, pac_id):
        limit = 50
        i = web.input(page=0)
        page = int(i.page)
        if 'filing_id' in i:
            p = [x.pac for x in schema.lob_pac_filings.select(where='filing_id=$i.filing_id',limit=limit, offset=page*limit, vars=locals())]
        elif pac_id:
            p = schema.lob_pac.select(where='id=$pac_id',limit=limit, offset=page*limit, vars=locals())
        else:
            p = schema.lob_pac.select(limit=limit, offset=page*limit)
        return render.lob_pacs(p,limit)
class lob_org:
    def GET(self, org_id):
        limit = 50
        i = web.input(page=0)
        page = int(i.page)
        if org_id:
            o = schema.lob_organization.select(where='id=$org_id', limit=limit, offset=page*limit, order='name asc', vars=locals())
        else:
            o = schema.lob_organization.select(limit=limit, offset=page*limit, order='name asc')
        return render.lob_orgs(o,limit)
class lob_person:
    def GET(self, person_id):
        limit = 50
        i = web.input(page=0)
        page = int(i.page)
        if person_id:
            p = schema.lob_person.select(where='id=$person_id', limit=limit, offset=page*limit, order='lastname asc', vars=locals())
        else:
            p = schema.lob_person.select(limit=limit, offset=page*limit, order='lastname asc')
        return render.lob_person(p,limit)

class politician_introduced:
    def GET(self, politician_id):
        try:
            pol = schema.Politician.where(id=politician_id)[0]
        except IndexError:
            raise web.notfound()
        return render.politician_introduced(pol)

class politician_groups:
    def GET(self, politician_id):
        related = group_politician_similarity(politician_id, qmin=1)
        try:
            pol = schema.Politician.where(id=politician_id)[0]
        except IndexError:
            raise web.notfound()
        return render.politician_groups(pol, related)

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
            raise web.notfound()
        if not r_safeproperty.match(what): raise web.notfound()

        #if `what` is not there in the `table` (provide available options rather than 404???)
        try:
            maxnum = float(db.select(table,
                                 what='max(%s) as m' % what,
                                 vars=locals())[0].m)
        except:
            raise web.notfound()

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
    assert table in table_map.values()
    if not r_safeproperty.match(what): raise web.notfound()
    
    item = db.query("select count(*) as position from %(table)s, \
      (select * from %(table)s where %(id_col)s=$id) as a \
      where %(table)s.%(what)s > a.%(what)s" % 
      {'table':table, 'what':what, 'id_col':id_col}, vars={'id': id})[0]
    return item.position + 1 # '#1' looks better than '#0'

class sparkdist:
    def GET(self, table, what):
        try:
            table = table_map[table]
        except KeyError:
            raise web.notfound()
        if not r_safeproperty.match(what): raise web.notfound()

        inp = web.input(point=None)
        points = db.select(table, what=what, order=what+' asc', where=what+' is not null')
        points = [x[what] for x in points.list()]

        web.header('Content-Type', 'image/png')
        return simplegraphs.sparkline(points, inp.point)

class staticdata:
    def GET(self, path):
        if not web.config.debug:
            raise web.notfound()

        assert '..' not in path, 'security'
        return file('data/' + path).read()

app = web.application(urls, globals())
def notfound():
    web.ctx.status = '404 Not Found'
    return web.notfound(getattr(render, '404')())

def internalerror():
    return web.internalerror(file('templates/500.html').read())

app.notfound = notfound
if production_mode:
    app.internalerror = web.emailerrors(config.send_errors_to, internalerror)

if __name__ == "__main__": app.run()
