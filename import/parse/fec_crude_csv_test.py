#!/usr/bin/python
# -*- coding: utf-8 -*-
import fec_crude_csv, doctest, cgitb
from cStringIO import StringIO

def records(inputstring):
    return list(fec_crude_csv.readfile(StringIO(inputstring)))

def test_endtext():
    """
    >>> records(filing_207928)
    ... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [{...'filer_id': 'C00410761', 'original_data': {...}...
    'committee': 'Castor for Congress', 'format_version': '5.3'...}]
    >>> records(truncated_filing)       # same
    ... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [{...'filer_id': 'C00410761', 'original_data': {...}...
    'committee': 'Castor for Congress', 'format_version': '5.3'...}]
    """

# Note the extra quote mark on the [ENDTEXT] line.
filing_207928 = '''"HDR","FEC","5.3","NGP Campaign Office(R)","1.0e","","","0",""
"F99","C00410761","Castor for Congress","P.O. Box 5419","","Tampa","FL","33675","Amy Martin","20060322","MST"
[BEGINTEXT]
March 22, 2006

Christopher A. Whyrick
Senior Campaign Finance Analyst
Federal Elections Commission
999 E Street, NW
Washington, DC 20463

Identification Number: C00410761

Reference: Year End Report (10/1/05-12/31/05)

Dear Mr. Whyrick,

	This letter is in response to the FEC request for additional information dated February 23, 2006.  As instructed in your letter, we have amended our Year End Report and corrected the discrepancy on Line 2 of FEC Form 3Z-1.

	If you need further assistance, please contact me at (813)251-5094.


Sincerely,



Amy Martin, Treasurer
Castor for Congress

[ENDTEXT]"
'''

# This is an invalid filing but it shouldn’t hang the importer.  (It
# did at one point; it would loop endlessly looking for [ENDTEXT].)
truncated_filing = '''"HDR","FEC","5.3","NGP Campaign Office(R)","1.0e","","","0",""
"F99","C00410761","Castor for Congress","P.O. Box 5419","","Tampa","FL","33675","Amy Martin","20060322","MST"
[BEGINTEXT]
March 22, 2006
'''

def test_v2_02_data():
    """We can’t handle version 2.x data yet, so we should just skip
    it until we find a spec for it.  Raising an exception is not
    acceptable.

    >>> records(filing_30458_truncated)
    []
    """

filing_30458_truncated = '''/* Header
FEC_Ver_# = 2.02
Soft_Name = Vocus, Inc. PACPRO
Soft_Ver# = 6.16.040
DEC/NODEC = DEC
Date_Fmat = CCYYMMDD
NameDelim = ^
Form_Name = F3XN
FEC_IDnum = C00238725
Committee = National Air Traffic Controllers Association PAC
Schedule_Counts:
SA11ai   = 00002
SB23     = 00023
/* End Header
"F3XN","C00238725","National Air Traffic Controllers Association PAC","1325 Massachusetts Ave., NW","","Washington","DC","20005","","X","M3","",,"",20020201,20020228,290018.35,45558.46,335576.81,23000,312576.81,0,0,332,45226.46,45558.46,0,0,45558.46,0,0,0,0,0,0,0,45558.46,45558.46,0,0,0,0,0,23000,0,0,0,0,0,0,0,0,0,23000,23000,45558.46,0,45558.46,0,0,0,250065.32,2002,91011.49,341076.81,28500,312576.81,534,90477.49,91011.49,0,0,91011.49,0,0,0,0,0,0,0,91011.49,91011.49,0,0,0,0,0,28500,0,0,0,0,0,0,0,0,0,28500,28500,91011.49,0,91011.49,0,0,0,"Mr. John Carr",20020323
"SA11ai","C00238725","IND","Glasserman^John^Mr.^Glasserman","4 Spruce Lane","","Essex Junction","VT","054524387","","","Federal Aviation Administration","Air Traffic Controller",404,,202,"15","","","","","","","","","","","","","","","Payroll Deduction ($101.00 Biweekly)","","10000072200300002"
'''

def test_windows_1252_characters():
    r"""The FEC claims that filings containing non-ASCII characters will be
    rejected, but here we have an example of a filing that wasn’t.  It
    contains a Windows-1252 byte.  Note that it is an en dash, not an
    em dash, sigh.  I am arbitrarily deciding that the result should
    be encoded in UTF-8.

    Note that this test doesn’t pass yet; the SKIP option to doctest
    was added in Python 2.5, so this test will barf 'has an invalid
    option' on 2.4.

    >>> records(filing_181941_truncated)[-1]
    ... #doctest: +SKIP
    {...'occupation': 'Team Ldr \xe2\x80\x93 HRIS'...}
    """

filing_181941_truncated = u'''"HDR","FEC","5.2","Vocus PAC Management","3.00.1828","","",0,""
"F3XN","C00083857","Occidental Petroleum Corporation Political Action Committee","10889 Wilshire Blvd.","","Los Angeles","CA","90024","","X","MY","",,"",20050101,20050630,48873.88,113149.90,162023.78,97411.13,64612.65,0.00,0.00,96058.37,16874.30,112932.67,0.00,0.00,112932.67,0.00,0.00,0.00,0.00,0.00,217.23,0.00,113149.90,113149.90,0.00,0.00,0.00,0.00,0.00,97000.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,411.13,97411.13,97411.13,112932.67,0.00,112932.67,0.00,0.00,0.00,48873.88,2005,113149.90,162023.78,97411.13,64612.65,96058.37,16874.30,112932.67,0.00,0.00,112932.67,0.00,0.00,0.00,0.00,0.00,217.23,0.00,113149.90,113149.90,0.00,0.00,0.00,0.00,0.00,97000.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,411.13,97411.13,97411.13,112932.67,0.00,112932.67,0.00,0.00,0.00,"Dominick^S.P.^^",20050722,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00
"SA11ai","C00083857","IND","","16919 PRESTON BEND DR","","DALLAS","TX","75248","","","Occidental Chemical Corp.","GM NGO/Laurel",400.00,20050429,400.00,"15","","","","","","","","","","","","","","","","","11109795","","","","","","SEWELL","LAWRENCE","R","",""
"SA11ai","C00083857","IND","","4001 VIA SOLANA","","P VERDES ESTATES","CA","90274","","","Occidental Petroleum Corp.","Dir Internal Audit",600.00,20050429,600.00,"15","","","","","","","","","","","","","","","","","11109790","","","","","","MISTRY","MARZI","J","",""
"SA11ai","C00083857","IND","","322 FAIRHAVEN CT","","NEWBURY PARK","CA","91320","","","Occidental Petroleum Corp.","Team Ldr  HRIS",350.00,20050429,350.00,"15","","","","","","","","","","","","","","","","","11109794","","","","","","PLACANICA","VINCENT","J","",""
'''.encode('iso-8859-1')
assert chr(0x96) in filing_181941_truncated # not really an ISO-8859-1
                                            # character! Windows-1252.

if __name__ == "__main__":
    cgitb.enable(format='text')
    doctest.testmod()
