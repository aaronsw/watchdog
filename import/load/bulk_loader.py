import os
import codecs
from types import NoneType

class bulk_loader_db:
    tables = {}
    db_name = None
    def __init__(self, db_name):
        self.db_name = db_name
    def open_table(self, table, columns, delete_first=False, filename=None):
        if table in self.tables: raise 'Table %s already open' % table
        self.tables[table] = bulk_loader(self.db_name, table, columns, delete_first, filename)
    def insert(self, table, seqname=None, _test=False, **values):
        if table not in self.tables: raise 'Table %s not open.' % table
        return self.tables[table].insert(table, seqname, _test, **values)

_text_encoding = 'latin-1'
#_text_encoding = 'utf-8'
class bulk_loader:
    """Opens a file/pipe and writes tsv."""
    hdr = "SET client_encoding = '%s';\nBEGIN;\n\n" % _text_encoding
    footer = "\.\n\nCOMMIT;\n\n"
    tsv_filename = psql_pipe = psql_out = use_file = cols = table = None
    def __init__(self, database_name, table, columns, delete_first=False, filename=None):
        """If filename is passed then write the tsv file. Otherwise pipe is opened to postgres."""
        self.use_file = self.tsv_filename = filename
        self.cols = columns
        self.table = table
        if not self.use_file:
            ## FIXME: better way to generate a unique name??
            self.tsv_filename = '/tmp/wd_loader.%s.%d.fifo' % (table, os.getpid())
            os.mkfifo(self.tsv_filename)
            # Open the psql end of pipe
            self.psql_pipe = os.popen('psql %s -f %s' % 
                    (database_name, 
                        self.tsv_filename), 'w')
        # Open our end of pipe
        self.psql_out = codecs.open(self.tsv_filename, 'w', _text_encoding)
        if delete_first:
            self.hdr += "DELETE from %s where 1=1;\n" % table
        copy_cmd = "COPY %s (%s) FROM stdin;" % (table, ', '.join(columns))
        print >>self.psql_out, self.hdr
        print >>self.psql_out, copy_cmd
    def insert(self, tablename, seqname=None, _test=False, **values): 
        assert(tablename == self.table)
        self.add_row(map(values.get, self.cols))
    def add_row(self, columns):
        def convert(x):
            if isinstance(x, NoneType):
                x = '\\N'
            if not isinstance(x, basestring):
                x = str(x)
            if not isinstance(x, unicode):
                x = unicode(x, _text_encoding)
            return x
        line = u'\t'.join([convert(x) for x in columns])
        print >>self.psql_out, line
    def __del__(self):
        if self.psql_out: 
            print >>self.psql_out, self.footer
            self.psql_out.close()
        if not self.use_file and self.tsv_filename:
            os.remove(self.tsv_filename)

