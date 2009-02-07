"""
parse data from govtrack.us
"""

#@@ implicit 110 assumption
STATS_XML = '../data/crawl/govtrack/us/110/repstats/%s.xml'
FEC_XML = '../data/crawl/govtrack/us/fec/campaigns-2008.xml'
METRICS = ['enacted', 'novote', 'verbosity', 'speeches', 
  'spectrum', 'introduced', 'cosponsor']

from xml.dom import pulldom
import web
import tools

from pprint import pformat, pprint

def parse_basics():
    dom = pulldom.parse(STATS_XML % 'people')
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
        dom = pulldom.parse(STATS_XML % metric)
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
    tools.export(parse_fec())
