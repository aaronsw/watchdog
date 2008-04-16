import web

urls = (
  '/blog/', 'index',
  '/blog/feed', 'feed',
  '/blog/(.*)', 'post',
)

render = web.template.render('templates/', base='base')

content = [
  web.storage(
    slug = 'momentum',
    title = 'Building Momentum',
    author = 'Aaron Swartz',
    updated = '2008-04-16T00:00Z',
    body = """
<p>
The response to the announcement of this little site 
has been bigger than I ever expected.
Within hours after I posted about it,
I'd received a couple dozen emails of support --
some people asking how they could help,
others asking sending their ideas and suggestions,
and many just saying "right on!"
</p>

<p>
I've launched dozens of sites but I've never gotten a response quite like this.
And I think it has to be chalked up to the power of this idea:
there are lots of people eager for a way to <em>get involved</em>.
If you want to do your part, 
I suggest you sign up for
<a href="http://groups.google.com/group/watchdog-volunteers">our volunteer list</a> -- 
I'll send an email out there when we need help with something.
</p>

<p>
Perhaps the most helpful -- 
and most unexpected -- 
piece has been all the Python programmers who wrote in 
asking how they could help.
The volunteers quickly ran thru everything I could think of off the top of my head
and I've had to go thru my todo list and start picking out things
I never thought I'd get to.
Of course that's a great problem to have
and <a href="http://watchdog.net/about/#feedback">we could always use more hands</a>.
</p>

<p>
And just a short while ago,
I did an interview with XM Satellite Radio about the project.
All in all, not bad for a first day.
</p>

<p>
Thanks to everyone who made it happen.
And let's make sure we don't lose this momentum -- 
together, let's build something great.
</p>
"""
  ),
  web.storage(
    slug = 'launch',
    title = 'Welcome to watchdog.net!',
    author = 'Aaron Swartz',
    updated = '2008-04-14T00:00:00Z',
    body = """
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
"""
  )
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
