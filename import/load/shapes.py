"""
load district shapes
"""
import simplejson as json
import web
import tools
from settings import db
from parse import shapes
from pprint import pprint

def load():
    for district in shapes.parse():
        outline = json.dumps({'type': 'MultiPolygon', 'coordinates': district['shapes']})
        if district['district']:
            district = tools.unfips(district['state_fipscode']) + '-' + district['district']
        else:
            district = tools.unfips(district['state_fipscode'])
        db.update('district', where='name=$district', outline=outline, vars=locals())

if __name__ == "__main__": load()
