"""Simple hack to generate a JSON 'database dump' without touching the database.
"""
import cgitb, fec, simplejson, sys

class DummyDB:
    def select(self, *args, **kwargs):
        return []
    def output(self, method, table, kwargs):
        print simplejson.dumps(dict(method=method, table=table, kwargs=kwargs))
    def update(self, table, **kwargs):
        self.output('update', table, kwargs)
    def insert(self, table, **kwargs):
        self.output('insert', table, kwargs)
    
if __name__ == '__main__':
    cgitb.enable(format='text')
    fec.db = DummyDB()
    fec.load_fec_efilings(sys.argv[1] if len(sys.argv) > 1 else None)
