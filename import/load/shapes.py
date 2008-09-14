"""
load district shapes
"""
import simplejson
import web
import tools
from settings import db
from parse import shapes

def load():
    for district in shapes.parse():
        outline = simplejson.dumps({'type': 'MultiPolygon', 'coordinates': district['shapes']})
        district = tools.unfips(district['state_fipscode']) + '-' + district['district']
        db.update('district', where='name=$district', outline=outline, vars=locals())

if __name__ == "__main__": load()
