"""
parse data from govtrack.us
"""

#@@ implicit 110 assumption
STATS_XML = '../data/crawl/govtrack/us/110/repstats/%s.xml'
METRICS = ['enacted', 'novote', 'verbosity', 'speeches', 
  'spectrum', 'introduced', 'cosponsored']

from xml.dom import pulldom
import web
import tools

def parse_basics():
    dom = pulldom.parse(STATS_XML % 'people')
    for event, node in dom:
        if event == "START_ELEMENT" and node.tagName == "person":
            out = web.storage(node.attributes.items())
            dom.expandNode(node)
            
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

if __name__ == "__main__":
    tools.export(parse_basics())
    tools.export(parse_speeches())
