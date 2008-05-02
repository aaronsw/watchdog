#!/usr/bin/env python
#
# A parser for the 2008 earmarks data (XLS format) from http://taxpayer.net/
# 
# This script depends on xls2list which will convert the excel file to a 2d array. 
# It then does some trivial parsing of each field and outputs the data in a few ways.
#
# author: Alex Gourley (acgourley@gmail.com)

import sys, re
from xls2list import *

HOUSE_REQUEST = 1
SENATE_REQUEST = 2
PRE_REDUCTION_AMT = 3
FINAL_AMOUNT = 4
BUDGET_REQUEST = 5
DESCRIPTION = 6
CITY_LOCATION=7
COUNTY=8
STATE=9
BILL=10
BILL_SECTION=11
BILL_SUBSECTION=12
PROJECT_HEADING=13
HOUSE_MEMBER = 14
HOUSE_PARTY = 15
HOUSE_STATE = 16
SENATE_MEMBER = 18
SENATE_PARTY= 19
SENATE_STATE = 20
PRESIDENTIAL_EARMARKS=21
UNDISCLOSED=22
INTENDED_RECIP=23
NOTES=24

class Earmark(object):
    houseRequestDollars = None
    senateRequestDollars = None
    preReductionAmountDollars = None
    finalAmountDollars = None
    budgetRequestDollars = None
    description = None
    cityLocation = None
    county = None
    state = None
    bill = None
    billSection = None
    billSubsection = None
    projectHeading = None
    houseMembers = []
    #housePartys = [] leaving out house and state, hoping we know this already with the name(s) alone
    #houseStates = []
    senateMembers = []
    #senatePartys = []
    #senateStates = []
    presidentialEarmarks = None
    undisclosed = None
    intendedRecipient = None
    notes = None
    
    def __init__(self):
        pass
    
    def __str__(self):
        result = ["============================="]
        for attr in dir(self):
            if attr.startswith("__"):
                continue
            result.append(attr +  ' = ' + str(self.__getattribute__(attr)))
        return "\n".join(result)


def earmarkFromRow(row):
    e = Earmark()
    e.houseRequestDollars = row[HOUSE_REQUEST]
    e.senateRequestDollars = row[SENATE_REQUEST]
    e.preReductionAmountDollars = row[PRE_REDUCTION_AMT]
    e.finalAmountDollars = row[FINAL_AMOUNT]
    e.budgetRequestDollars = row[BUDGET_REQUEST]
    e.description = row[DESCRIPTION]
    e.cityLocation = row[CITY_LOCATION]
    e.county = row[COUNTY]
    e.state = row[STATE]
    e.bill = row[BILL]
    e.billSection = row[BILL_SECTION]
    e.billSubsection = row[BILL_SUBSECTION]
    e.projectHeading = row[PROJECT_HEADING]
    if isinstance(row[HOUSE_MEMBER], basestring):
        e.houseMembers = [x.strip() for x in row[HOUSE_MEMBER].split(';')]
    if isinstance(row[SENATE_MEMBER], basestring):
        e.senateMembers = [x.strip() for x in row[SENATE_MEMBER].split(';')]
    e.presidentialEarmarks = row[PRESIDENTIAL_EARMARKS]
    e.undisclosed = row[UNDISCLOSED]
    e.intendedRecipient = row[INTENDED_RECIP]
    e.notes = row[NOTES]
    return e

def getEarmarks(xlsFilename):
    """Break down the xls into a 2d data array, stripping off first rows which do not have data."""
    data = xls2list(xlsFilename)
    marks = []
    for row in data[3:]:
        marks.append(earmarkFromRow(row))
    return marks
    
def getEarmarksByName(xlsFilename):
    """Take rows (like those returned from getEarmarks) and hash them by representative. If no representative is listed
    then the earmark will be hashed under the "noname" key."""
    marks = getEarmarks(xlsFilename)
    byPerson = {}
    byPerson["noname"] = []
    for row in marks:
        people = row.houseMembers+row.senateMembers
        if len(people) == 0:
            byPerson["noname"].append(row)
        for person in people:
            if person in byPerson:
                byPerson[person].append(row)
            else:
                byPerson[person] = [row]
    return byPerson

def printEarmarks(rows):
    """Takes in an array of rows (like those produced from getEarmarks) and pretty prints them."""
    for row in rows:
        print row

#Examples of how to use, assuming the path to the earmarks file is passed in as the first arg.

#marks = getEarmarksByName(sys.argv[1])
#printEarmarks(marks["noname"])
#printEarmarks(marks["Edwards"])

if __name__ == "__main__":
    import simplejson
    earmarks = getEarmarks('../data/crawl/taxpayer/bigkahuna.xls')
    print simplejson.dumps([x.__dict__ for x in earmarks], indent=2, sort_keys=True)
