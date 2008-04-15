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
    'updated': '2008-04-14T00:00:00Z',
    'body': """
<p>
It's a big election year in the US, 
which means a lot of people have been thinking about politics lately. 
I've been far from immune, 
signing up for dozens of sites and reading bunches of blogs. 
But, despite all this, 
I feel like there's something missing: 
a way for the average person to actually <em>get involved</em> in politics.
</p>

<p>
Sure, you can be outraged over some factoid you read on a blog 
or take part in some action campaign started by a nonprofit,
but that still feels like being a spectator to me. 
Instead, I wanted to a site where you could discover the facts for yourself 
and start your own action campaigns.
</p>

<p>
Not finding one, I've decided to help build it. 
<a href="http://watchdog.net/about#people">An amazing group of people</a> 
have signed on with me 
(<a href="http://watchdog.net/about#help">although we're still looking for more</a>) 
and the Sunlight Network given us a grant to fund it.
</p>

<p>
You can read more about us and our plans on 
<a href="http://watchdog.net/about/">the about page</a> 
but for now let me just say welcome and pardon the mess. 
We're trying to develop this site fast and in public, 
so expect lots of changes. 
We'll try to keep the public brokenness to a minimum, 
but there will undoubtedly be some, 
especially these first few weeks.
</p>

<p>
And to forestall the inevitable catcalls: 
yes, there's not much here now. 
But we literally started officially working <em>today</em>. 
This is just the skeleton of the site we hope to build.
</p>

<p>
Thanks for bearing with us 
and <a href="http://watchdog.net/about/#feedback">let us know what you think</a>.
</p>
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
        lastupdate = max(x.updated for x in content)
        return render._do('blog_feed')(content, lastupdate)

class post:
    def GET(self, name):
        if name in content_mapping:
            return render.blog_post(content_mapping[name])
        else:
            raise web.notfound

app = web.application(urls, globals())
