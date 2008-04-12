import web

urls = (
  '/blog/', 'index',
  '/blog/feed', 'feed',
  '/blog/(.*)', 'post',
)

render = web.template.render('templates/', base='base')

content = [
  web.storage({
    'slug': 'launch',
    'title': 'Welcome to watchdog.net!',
    'author': 'Aaron Swartz',
    'date': '2008-04-11',
    'body': """
<p>So we're starting a new website. You can read all about us and our plans on <a href="/about/">the about page</a> but here I mostly wanted to welcome you and apologize for the mess. We're trying to develop this site fast and in public, so expect lots of changes. We'll try to keep the public brokenness to a minimum, but there will undoubtedly be some, especially these first few weeks.</p>

<p>Thanks for bearing with us and <a href="/about/#feedback">let us know what you think</a>.</p>
""",
  })
]
content_mapping = dict((x.slug, x) for x in content)

class index:
    def GET(self):
        return render.blog_index(content)

class feed:
    def GET(self):
        web.header('content-type', 'application/atom+xml')
        return render._do('blog_feed')(content)

class post:
    def GET(self, name):
        if name in content_mapping:
            return render.blog_post(content_mapping[name])
        else:
            raise web.notfound

app = web.application(urls, globals())
