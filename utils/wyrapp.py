"""
web interface to Write Your Rep 
"""
import web
import forms, helpers, auth
from users import fill_user_details, update_user_details
from wyrutils import *
from settings import db, render
import writerep
import simplejson

urls = (
    '/', 'write_rep',
    '/getcaptcha', 'get_captchas',
    '/verifyzip', 'verify_zip'
)

def captcha_box(pol, img_src):
    name = 'captcha_%s' % pol
    pre = "<img src='%s'/>" % img_src
    return web.form.Textbox('captcha_%s' % pol, web.form.notnull,
	        web.form.Validator("Enter the letters as they are shown in the image", bool), 
	        size='10', pre=pre, description='Validation')
    
def render_captcha(c):
    return """<tr><td colspan=3>
                <label for='%s'>Verification</label> %s %s 
                </td></tr>""" % (c.name, c.pre, c.render())

def add_captcha(form, img_src, pol):
    c = captcha_box(pol, img_src)   
    form.inputs = list(form.inputs) + [c]
    return render_captcha(c)

def prepare_for_captcha(wf, pols=None):
    env = {}
    captcha_html = ''
    if not pols:
        address = (wf.addr1.value or '') + (wf.addr2.value or '')
    	pols = getpols(wf.zip5.value, wf.zip4.value, address)
    for pol in pols:
    	if has_captcha(pol):
    	    e = writerep.prepare(pol)
    	    if e:
                captcha_html += add_captcha(wf, e['captcha_src'], pol)
                env[pol] = e
    if env:
        wf.captcha_env.value = simplejson.dumps(env)
    return captcha_html

class write_rep:
    def GET(self, wf=None):
        u = helpers.get_user()
        uemail = u and u.email
        if not wf:
    	    #create a new form and initialize with current user details
            wf = forms.wyrform()
    	    u and fill_user_details(wf, u)
    	captcha_html = prepare_for_captcha(wf)
    	msg, msg_type = helpers.get_delete_msg()
    	return render.writerep(wf, useremail=uemail, captchas=captcha_html, msg=msg)

    def POST(self):
        def pol_link(polid):
            p = db.select('politician', what='firstname, middlename, lastname',
                            where='id=$polid', vars=locals())[0]
            return '<a href="/p/%s">%s %s %s</a>' % (polid, p.firstname or '',
                            p.middlename or '', p.lastname or '')
                
    	i = web.input()
    	wf = forms.wyrform()
    	pols = getpols(i.zip5, i.zip4, i.addr1+i.addr2)
    	captcha_needed = require_captcha(i, pols)
    	if not wf.validates(i) or captcha_needed:
            if captcha_needed: wf.valid, wf.note = False, 'Please fill the captcha below'
    	    wf.fill(i)
    	    return self.GET(wf)
    	else:
    	    uid = auth.assert_login(i)
    	    update_user_details(i, uid)
    	    env = simplejson.loads(i.get('captcha_env', '{}'))
    	    status = writerep.send_msgs(uid, i, source_id='wyr', pols=pols, env=env)
    	    pol_str = ", ".join([pol_link(p) for p in pols])
    	    helpers.set_msg('Your message has been sent to %s' % pol_str)
    	    raise web.seeother('/')

class get_captchas:
    def GET(self):
        i = web.input()
        pols = dist2pols(i.get('dist'))
        wf = forms.wyrform()
        captcha_html = prepare_for_captcha(wf, pols)
        return captcha_html

class verify_zip:
    def GET(self):
        i = web.input()
        dists = getdist(i.zip5, i.zip4, i.address)
        if len(dists) == 1:
            return dists[0]
        else:
            return len(dists)

app = web.application(urls, globals())
if __name__ == "__main__":
    app.run()