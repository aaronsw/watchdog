"""Simple hack to generate a JSON 'database dump' without touching the database.
"""
import cgitb, fec, simplejson, sys

class DummyDB:
    def select(self, *args, **kwargs):
        return []
    def output(self, method, args, kwargs):
        print "db.%s %s %s" % (method,
                               simplejson.dumps(args),
                               simplejson.dumps(kwargs))
    def update(self, *args, **kwargs):
        self.output('update', args, kwargs)
    def insert(self, *args, **kwargs):
        self.output('insert', args, kwargs)
    
if __name__ == '__main__':
    cgitb.enable(format='text')
    fec.db = DummyDB()
    fec.load_fec_efilings(sys.argv[1] if len(sys.argv) > 1 else None)
