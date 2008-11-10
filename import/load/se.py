"""
Xapian importer.
"""
try:
    import xappy
except ImportError:
    import sys, warnings
    warnings.warn('No xappy found. Skipping search engine stuff.')
    sys.exit(0)
import schema

DBPATH = '../se'

def replacetable(s, tab):
    for k, v in tab.iteritems():
        s = s.replace(k, v or '')
    return s

def index(doc, k, v):
    return doc.fields.append(xappy.Field(k, v))

def trash(db):
    for k in db.iterids():
        db.delete(k)

nameformats = """
first middle last
first last
nickname last
last, first
last, first middle
last, nickname
""".strip()

def initdb():
    iconn = xappy.IndexerConnection(DBPATH)
    trash(iconn)
    iconn.add_field_action('name', xappy.FieldActions.INDEX_FREETEXT, spell=True)
    iconn.add_field_action('id', xappy.FieldActions.INDEX_FREETEXT)
    iconn.add_field_action('id', xappy.FieldActions.STORE_CONTENT)
    return iconn

def load_pols(iconn):
    pols = schema.Politician.select()
    for p in pols:
        doc = xappy.UnprocessedDocument()
        for format in nameformats.split('\n'):
            text = replacetable(format, 
              dict(first=p.firstname, middle=p.middlename, last=p.lastname, nickname=p.nickname))
            index(doc, 'name', text)
        index(doc, 'name', p.id.replace('_', ' '))
        index(doc, 'id', p.id)
        iconn.add(doc)

def test():
    sconn = xappy.SearchConnection(DBPATH)
    print sconn.get_doccount(), 'documents loaded.'
    def query(qtext):
        q = sconn.query_parse(sconn.spell_correct(qtext), default_op=sconn.OP_AND)
        return [x.data['id'][0] for x in sconn.search(q, 0, 10)]

    assert query('biden joe') == ['joe_biden']
    assert query('barak obma') == ['barack_obama']
    return True

if __name__ == "__main__":
    iconn = initdb()
    load_pols(iconn)
    iconn.flush()
    iconn.close()
    
    if test(): print 'Success.'