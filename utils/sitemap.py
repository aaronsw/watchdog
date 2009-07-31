"""Script to generate XML sitemap of openlibrary.org website.
"""

import web
import os
import itertools
import datetime

import webapp
from index import getindex

t_sitemap = """$def with (items)
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    $for i in items:
        <url>
            <loc>http://watchdog.net$i</loc>
        </url>
</urlset>
"""

t_siteindex = """$def with (names, timestamp)
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    $for x in names:
        <sitemap>
            <loc>http://watchdog.net/static/sitemaps/sitemap_${x}.xml.gz</loc>
            <lastmod>$timestamp</lastmod>
        </sitemap>
</sitemapindex>
"""

sitemap = web.template.Template(t_sitemap)
siteindex = web.template.Template(t_siteindex)

def write(path, text):
    from gzip import open as gzopen
    print 'writing', path, text.count('\n')
    f = gzopen(path, 'w')
    f.write(text)
    f.close()

def make_siteindex():
    groups = web.group(getindex(webapp.app), 50000)
    
    if not os.path.exists('sitemaps'):
        os.mkdir('sitemaps')
    
    for i, x in enumerate(groups):
        write("sitemaps/sitemap_%04d.xml.gz" % i, str(sitemap(x)))
    names = ["%04d" % j for j in range(i)]
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    index = siteindex(names, timestamp)
    write("sitemaps/siteindex.xml.gz", index)
        
if __name__ == "__main__":
    make_siteindex()

