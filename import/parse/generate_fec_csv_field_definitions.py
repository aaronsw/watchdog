# -*- coding: utf-8; -*-
"""Generates CSV file of FEC field definitions.

This regenerates e.g. the `watchdog/import/parse/fec_headers/5.1.csv`
file from the `Fec_v510.xls` spreadsheet provided by the FEC.  It
doesn’t completely work yet, because I’m not quite sure what to do
about form 12; also, it omits form 3Z-1 entirely because the
spreadsheet doesn’t contain any field definitions for it.

Instructions for use:

    python2.5 generate_fec_csv_field_definitions.py \
        ~/docs/FEC_v5.x/Fec_v510_revised_by_kragen.xls > fec_headers/5.1.csv

I really thought this would be about 5 lines of code.

"""

import pyExcelerator, sys

def numeric_cells_in_column_a(sheet):
    """Generates ((row, col), value) tuples for numeric cells in column A.

    Not in order.

    This is useful because column A contains the sequence number for
    the (filing) columns we’re looking for.
    """
    return (((row, col), value) for (row, col), value in sheet[1].items()
            if col == 0 and type(value) is not unicode)
 
def get_field_names(sheet):
    """Outputs the field names for a particular sheet.
    """
    sheetname, cells = sheet

    current_field_number = 0
    field_names = []
    for (row, col), value in sorted(numeric_cells_in_column_a(sheet)):
        if value != current_field_number + 1:
            # This still fails on F12, because a bunch of fields are omitted!
            # It found an error in Sch I in the FEC’s version of
            # Fec_v510.xls and Fec_v500.xls; I’m running from a
            # corrected one.
            # XXX maybe do something better than just omit it?
            sys.stderr.write(("in sheet %s, field %d " +
                              "follows field %d; omitting this sheet\n") % (
                sheetname, value, current_field_number))
            return
        current_field_number = value
        field_names.append(cells[row, 1])
    print ';'.join([sheetname.replace('Sch ', 'S').upper()] + field_names)

def sheets_having_col_seq(sheets):
    """Sheets describing a record format say COL SEQ in the first column,
    in the first few rows.  This generator finds those sheets.

    """
    for name, cells in sheets:
        for row in range(20):
            if cells.get((row, 0)) == 'COL':
                assert cells.get((row+1, 0)) == 'SEQ'
                yield name, cells
                break
        else:
            sys.stderr.write("sheet %s has no COL SEQ; omitting this sheet\n"
                             % name)

def get_all_field_names(sheets):
    """Outputs the field names for all record types."""
    for sheet in sheets_having_col_seq(sheets): get_field_names(sheet)

if __name__ == '__main__':
    get_all_field_names(pyExcelerator.parse_xls(sys.argv[1]))
