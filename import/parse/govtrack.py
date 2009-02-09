"""
parse data from govtrack.us
"""

from settings import current_session

STATS_XML = '../data/crawl/govtrack/us/%s/repstats/' % current_session + '%s.xml'
FEC_XML = '../data/crawl/govtrack/us/fec/campaigns-2008.xml'
METRICS = ['enacted', 'novote', 'verbosity', 'speeches', 
  'spectrum', 'introduced', 'cosponsor']

from xml.dom import pulldom
import web
import tools
import glob

def parse_basics():
    for fn in glob.glob(STATS_XML % 'people'):
        dom = pulldom.parse(fn)
        for event, node in dom:
            if event == "START_ELEMENT" and node.tagName == "person":
                out = web.storage(node.attributes.items())
                dom.expandNode(node)
                out.roles = map(lambda r: web.storage(r.attributes.items()), node.getElementsByTagName('role'))
                
                if out.get('district'):
                    out.represents = out.state + '-' + out.district.zfill(2)
                else:
                    if out.get('state'):
                        out.represents = out.state
                        assert out.title == 'Sen.'
                
                if 'current-committee-assignment' in [
                  hasattr(x, 'tagName') and x.tagName for x in node.childNodes
                ]:
                    out.active = True

                yield out

def parse_stats(metrics=METRICS):
    for metric in metrics:
        for fn in glob.glob(STATS_XML % metric):
            try:
                dom = pulldom.parse(fn)
            except IOError:
                continue
            for event, node in dom:
                if event == "START_ELEMENT" and node.tagName == 'representative':
                    yield web.storage(node.attributes.items())

def parse_fec():
    dom = pulldom.parse(FEC_XML)
    for event, node in dom:
        if event == "START_ELEMENT" and node.tagName == 'candidate':
            dom.expandNode(node)
            fec_id = node.getElementsByTagName('id')[0].firstChild.nodeValue
            uri = node.getElementsByTagName('uri')[0].firstChild.nodeValue
            if fec_id in uri: continue
            bioguide_id = uri.split('/')[-1]
            yield {'fecid': fec_id, 'bioguideid': bioguide_id}

if __name__ == "__main__":
    tools.export(parse_basics())
    tools.export(parse_stats())
    if current_session == 110: tools.export(parse_fec())
