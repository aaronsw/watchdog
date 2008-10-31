import web
from settings import render
urls = (
  '', 'reblog',
  '/', 'index',
  '/feed', 'feed',
  '/(.*)', 'post',
)

content = [
  web.storage(
    slug='fecpvs',
    title='More data!',
    author='Aaron Swartz',
    updated='2008-07-30T00:00:00Z',
    body = """
<p>
We've added even more data to the site. 
Now politician pages 
feature data from the FEC -- 
the Federal Election Commission,
which tracks all usage of money in politics.
FEC data includes things like
the amount of money raised,
who it was raised from,
and so on.
We hope to have even more
(actually, a lot more)
FEC data soon, 
but hopefully this provides an interesting start.
</p>

<p>
We've also added some more personal data
from our friends over at <a 
  href="http://votesmart.org"
>Project Vote Smart</a>.
The data includes things like
a politician's nickname
and educational history,
all of which we now provide on politician pages.
</p>

<p>
I hope you enjoy the new features 
and stay tuned for some even more exciting stuff tonight
and later this week.
</p>
    """
  ),
  web.storage(
    slug = 'alignment',
    title = 'Interest Group Alignment',
    author = 'Aaron Swartz',
    updated = '2008-06-16T00:00:00Z',
    body = """
<p>
First, 
let me say welcome aboard to our newest team member,
programmer A.S.L. Devi. 
Devi's already proved herself invaluable 
by building our latest feature:
politician&mdash;interest group alignment.
It's a terrible name
(my fault; let me know if you have a better one)
but the idea is simple:
go to a page like 
<a href="http://watchdog.net/p/mark_kirk">Mark Kirk's</a>
and scroll to the bottom.
There you'll see that Kirk is a big fan of people like
the National Association of Home Builders and
the National Association of Realtors,
but not the American Civil Liberties Union.
And for each group you can click 
and see the votes where they agree and disagree.
</p>

<p>
Furthermore, 
if you click on a bill and scroll to the bottom,
you can see all the groups that supported or opposed the bill.
</p>

<p>
It's pretty fun stuff and, 
in my opinion,
awfully exciting.
It's all made possible thanks to our partners:
<a href="http://www.govtrack.us/">GovTrack.us</a>, 
a fantastic site which provides data on bills, and
<a href="http://www.maplight.org/">MAPLight.org</a>, 
a Berkeley non-profit which each summer
(including right now)
brings interns out to search the news 
to see who is supporting and opposing 
the bills currently before Congress.
</p>

<p>
Thanks to everyone who made this happen.
I hope you enjoy it!
</p>
"""
  ),
  web.storage(
    slug = 'earmarks',
    title = 'Earmark Info',
    author = 'Aaron Swartz',
    updated = '2008-05-07T00:00:00Z',
    body = """
<p>
Thanks to the work of Alex Gourley
and data from <a href="http://taxpayer.net/">Taxpayers for Common Sense</a>,
politician pages now have basic information
about the earmarks they've requested:
the size and number requested
and the size and number eventually passed.
</p>

<p>
"Earmark" is the catch-all term for the requests
that Congresspeople attach to bills requiring Federal money
be given to particular people or places.
They've been in the news a lot lately,
criticized as a form of corruption 
in which Congresspeople hand out money to lobbyists or campaign contributors
instead of letting civil servants or the bidding process handle it.
</p>

<p>
As with other Congressional perks,
they're not exactly distributed evenly.
<a href="http://watchdog.net/p/by/amt_earmark_received">Our chart</a>
shows how House leaders like 
<a href="http://watchdog.net/p/nancy_pelosi">Nancy Pelosi</a>
come out on top,
with hundreds of millions of dollars in earmarks,
while newcomers like 
<a href="http://watchdog.net/p/laura_richardson">Laura Richardson</a>
get only hundreds of thousands.
</p>

<p>
Whatever your feelings on earmarks,
we hope this data is interesting to you.
Thanks to Alex and Taxpayers for Common Sense for making it possible.
</p>
"""
  ),
  web.storage(
    slug = 'speeches',
    title = 'Speech Data',
    author = 'Aaron Swartz',
    updated = '2008-04-21T00:00:00Z',
    body = """
<p>
I'm thrilled to say that Thursday, 
just days after we launched, 
we got our first volunteer code contribution.
Didier Deshommes created 
<a href="http://github.com/dfdeshom/watchdog/">a branch on github</a>,
added support for parsing some data about speeches politicians have made,
and I pulled it and added it to the site.
</p>

<p>
Now when you visit a page like 
<a href="http://watchdog.net/p/nancy_pelosi">Nancy Pelosi</a>
you can see how many times she's spoken this session
and the average length of her speech.
</p>

<p>
It's great to see these kinds of contributions and 
I know there are more in the pipeline!
Thanks to everyone who's been pitching in.
</p>

<p>
On a darker note, 
apologies for the outages over the weekend. 
I think I discovered the cause of the problem
and it shouldn't happen again.
</p>
"""
  ),
  web.storage(
    slug = 'momentum',
    title = 'Building Momentum',
    author = 'Aaron Swartz',
    updated = '2008-04-16T23:48:00Z',
    body = """
<p>
The response to the announcement of this little site 
has been bigger than I ever expected.
Within hours after I posted about it,
I'd received a couple dozen emails of support --
some people asking how they could help,
others sending their ideas and suggestions,
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
        return render._template('blog_feed')(content, lastupdate)

class post:
    def GET(self, name):
        if name in content_mapping:
            return render.blog_post(content_mapping[name])
        else:
            raise web.notfound

class reblog:
    def GET(self):
        raise web.seeother('/')

app = web.application(urls, globals())
