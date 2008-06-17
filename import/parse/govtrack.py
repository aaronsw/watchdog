"""
parse data from govtrack.us

from: data/crawl/govtrack/people.xml
"""

PEOPLE_XML = '../data/crawl/govtrack/people.xml'

from xml.dom import pulldom
import web
import tools

def parse():
    dom = pulldom.parse(PEOPLE_XML)
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

if __name__ == "__main__": tools.export(parse())
