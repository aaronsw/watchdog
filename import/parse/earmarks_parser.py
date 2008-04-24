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
SENATE_MEMBER = 17
SENATE_PARTY=18
SENATE_STATE = 19
PRESIDENTIAL_EARMARKS=20
UNDISCLOSED=21
INTENTED_RECIP=22
NOTES=23

filename = sys.argv[1]
data = xls2list(filename)

class Earmark:
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


def earmarkFromRow(row):
    e = Earmark()
    e.houseRequest = row[HOUSE_REQUEST]
    e.senateRequest = row[SENATE_REQUEST]
    #etc
def count_earmarks(data,type=HOUSE_MEMBER):
	earmarks,pra_total,final_total = {},{},{}
	for row in data[3:]:
		if row[type] is None:
			continue
		members = row[type]
		members = re.split(",|;", str(members))
		for member in members:
			member = member.strip()
			earmarks[member] = earmarks.get(member, 0) + 1
			if row[PRE_REDUCTION_AMT] is None:
				continue
			pra_total[member] = pra_total.get(member, 0) + float(row[PRE_REDUCTION_AMT])
			if row[FINAL_AMT] is None:
				continue
			final_total[member] = final_total.get(member, 0) + float(row[FINAL_AMT])
	return (earmarks,pra_total,final_total)

def order_by_highest(d):
	sorted_count = [(v,k) for k, v in d.items()]
	sorted_count.sort()
	sorted_count.reverse()
	return [(k, v) for v, k in sorted_count]

earmarks,pra_total,final_total = count_earmarks(data)
