# -*- coding: utf-8; -*-
"""OpenOffice.org macro definition: generates CSV file of FEC field definitions.

This regenerates e.g. the `watchdog/import/parse/fec_headers/5.1.csv`
file from the `Fec_v510.xls` spreadsheet provided by the FEC.  It
doesn’t completely work yet, because I’m not quite sure what to do
about form 12.  Also it omits form 3Z-1 entirely because the
spreadsheet doesn’t contain any field definitions for it.

Instructions for use: (this is painful because of OpenOffice UI brain
damage)

- copy or symlink this file into your OpenOffice.org Python scripts
  directory.  On Unix with OpenOffice.org 2.x, that will be
  `~/.openoffice.org2/user/Scripts/python`, which you may need to
  create.
- open the Excel spreadsheet in OpenOffice.org Calc.
- select Tools → Macros → Run Macro... from the menu
- in the “Macro Selector” dialog box that comes up, expand out “My
  Macros”; there should be an item there named
  “generate_fec_csv_field_definitions”, created by the existence of
  this file in that directory.
- click on that item.
- in the right pane, click on “get_all_field_names”, one of the three
  items displayed.
- click the “Run” button on the right of the dialog box.

If all goes well, which it won’t because of form 12, the script will
silently execute.  In any case, it will append its semicolon-separated
results to a file called “tmp.debuglog” in your home directory.

I really thought this would be about 5 lines of code.

"""

import os, uno
from com.sun.star.table.CellContentType import VALUE, FORMULA
# TEXT and EMPTY also show up from CellContentType.


### The first few things here are fairly generic,
### non-application-specific attempts to paper over the
### overcomplicated brain damage that is the OOo API.

class FunctionCaller:
    """Makes it easier to call functions in an OOo spreadsheet.

    Usage:
    f = FunctionCaller(uno.getComponentContext().ServiceManager)
    print f.count(sheet.getCellRangeByName('A1:A9999'))
    """
    def __init__(self):
        servicemanager = uno.getComponentContext().ServiceManager
        self._funcservice = servicemanager.createInstance('com.sun.star.sheet.FunctionAccess')
    def __getattr__(self, name):
        return FunctionProxy(self._funcservice, name)

class FunctionProxy(object):
    """Helper class for FunctionCaller."""

    def __init__(self, funcservice, name):
        """
        - `funcservice`: the com.sun.star.sheet.FunctionAccess object
        - `name`: the name of the function to call
        """
        self._funcservice = funcservice
        self._name = name
    def __call__(self, *args):
        return self._funcservice.callFunction(self._name, args)

def ActiveSheet():
    """Returns the currently active sheet in a Calc spreadsheet."""
    return XSCRIPTCONTEXT.getDocument().CurrentController.ActiveSheet

def Range(range, sheet=None):
    """Returns the specified range in a oocalc sheet,
    by default the current one.
    """
    return (sheet or ActiveSheet()).getCellRangeByName(range)

def Sheets():
    """A generator of the sheets in the current spreadsheet doc."""
    sheets = XSCRIPTCONTEXT.getDocument().Sheets
    for sheetname in sheets.ElementNames:
        yield sheets.getByName(sheetname)


### stuff specific to FEC spreadsheets follows

def debug(athing):
    """Write `athing` to ~/tmp.debuglog."""
    file('%s/tmp.debuglog' % os.getenv('HOME'), 'a').write('%s\n' % athing)

def count_cells_in_column_a(sheet=None):
    """Counts the cells in column A of the current sheet that contain a number.

    Includes formulas.

    This is useful because column A contains the sequence number for
    the columns we’re looking for.
    """
    f = FunctionCaller()    # is it safe to build this at import time instead?
    rv = f.count(Range("A1:A9999", sheet)) # note that this is floating-point.
    return rv

def get_field_names(sheet=None):
    """Outputs the field names for a particular sheet to the debug log.
    """
    if sheet is None: sheet = ActiveSheet()
    count = count_cells_in_column_a(sheet)
    row = 0
    current_field_number = 0
    field_names = []
    # asking for rows past 65535 crashes OOo, so we limit this in case
    # there’s another bug that causes us to not get the right field names
    while len(field_names) < count and row < 10000: 
        cell = sheet.getCellByPosition(0, row)
        if cell.Type in [VALUE, FORMULA]: # the ones counted by =COUNT()
            field_number = cell.Value
            # this still fails on F12, because a bunch of fields are omitted!
            # XXX have to figure out what to do
            assert field_number == current_field_number + 1, (sheet.Name, row)
            current_field_number = field_number
            field_names.append(sheet.getCellByPosition(1, row).String)
        row += 1
    debug(';'.join([sheet.Name] + field_names))

def sheets_having_col_seq():
    """Sheets describing a record format say COL SEQ in the first column,
    in the first few rows.  This generator finds those sheets."""
    for sheet in Sheets():
        for row in range(20):
            if sheet.getCellByPosition(0, row).String == 'COL':
                yield sheet
                break

def list_sheets_having_col_seq():
    """Output to the debug log the names of sheets defining record types."""
    debug([sheet.Name for sheet in sheets_having_col_seq()])

def get_all_field_names():
    """Outputs the field names for all record types to the debug log."""
    for sheet in sheets_having_col_seq(): get_field_names(sheet)

# This controls what OOo displays in the UI as available macros.
g_exportedScripts = (get_all_field_names,
                     get_field_names,
                     list_sheets_having_col_seq)
