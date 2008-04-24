#!/usr/bin/env python
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
    houseRequest = None
    senateRequest = None
    preReductionAmount = None
    finalAmount = None
    budgetRequest = None
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
    e.houseRequest = row[HOUSE_REQUEST]
    e.senateRequest = row[SENATE_REQUEST]
    e.preReductionAmount = row[PRE_REDUCTION_AMT]
    e.finalAmount = row[FINAL_AMOUNT]
    e.budgetRequest = row[BUDGET_REQUEST]
    e.description = row[DESCRIPTION]
    e.cityLocation = row[CITY_LOCATION]
    e.county = row[COUNTY]
    e.state = row[STATE]
    e.bill = row[BILL]
    e.billSection = row[BILL_SECTION]
    e.billSubsection = row[BILL_SUBSECTION]
    e.projectHeading = row[PROJECT_HEADING]
    if isinstance(row[HOUSE_MEMBER], basestring):
        e.houseMembers = re.split("[ ;,]+", row[HOUSE_MEMBER])
    if isinstance(row[SENATE_MEMBER], basestring):
        e.senateMembers = re.split("[ ;,]+", row[SENATE_MEMBER])
    e.presidentialEarmarks = row[PRESIDENTIAL_EARMARKS]
    e.undisclosed = row[UNDISCLOSED]
    e.intendedRecipient = row[INTENDED_RECIP]
    e.notes = row[NOTES]
    return e

def getEarmarks(xlsFilename):    
    data = xls2list(xlsFilename)
    marks = []
    for row in data[3:]:
        marks.append(earmarkFromRow(row))
    print data[4]
    map(lambda m: sys.stdout.write(str(m)+'\n'),  marks[0:1])

marks = getEarmarks(sys.argv[1])


