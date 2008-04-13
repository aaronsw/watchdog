"""
parse data from govtrack.us

from: data/crawl/govtrack/people.xml
"""

import web
from xml.sax import make_parser, handler

class PeopleXML(handler.ContentHandler):
    def __init__(self, callback):
        self.callback = callback
        self.current = None
        
    def startElement(self, name, attrs):
        if name == 'person':
            self.current = web.storage(attrs)
            if self.current.get('district'):
                self.current.represents = self.current.state + '-' + self.current.district.zfill(2)
            else:
                if self.current.get('state'):
                    self.current.represents = self.current.state
                    assert self.current.title == 'Sen.'
        if name == 'current-committee-assignment':
            self.current.active = True
    
    def endElement(self, name):
        if name == 'person':
            self.callback(self.current)
            self.current = None

def callback(pol):
    if pol.get('active', False):
        print pol.represents

def main(callback):
    parser = make_parser()
    parser.setContentHandler(PeopleXML(callback))
    parser.parse('../data/crawl/govtrack/people.xml')

if __name__ == "__main__": main(callback)
