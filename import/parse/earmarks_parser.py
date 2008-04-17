#!/usr/bin/env python
import sys, re
from xls2list import *





HOUSE_MEMBER = 14
HOUSE_STATE = 16
SENATE_MEMBER = 18
SENATE_STATE = 20

filename = sys.argv[1]
data = xls2list(filename)
house = {}
senate = {}

print data[2]
for row in data[2:]:
        #look at house
        hMembers = row[SENATE_MEMBER]
        if hMembers == None:
                continue
        print hMembers
        hMembers = re.split(",|;", str(hMembers))
        if len(hMembers) > 1:
                continue
        member = hMembers[0].strip()
        if house.has_key(member):
                if house[member] != row[SENATE_STATE]:
                        print "mismatch!"
        else:
                house[member] = row[SENATE_STATE]
print len(house)
print house
