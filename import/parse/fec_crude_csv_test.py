#!/usr/bin/python
# -*- coding: utf-8 -*-
import fec_crude_csv, doctest, cgitb

def records(inputstring):
    return list(fec_crude_csv.readstring(inputstring))

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
    ... #doctest: +ELLIPSIS
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

def test_candidate_name():
    """There are a variety of fields from which we can extract
    candidate names.  This tests some of them.

    This is from the committee name 'KT McFarland for Congress':
    >>> fec_crude_csv.read_filing(filing_230174_truncated,
    ...                           '230174.fec')['candidate']
    'KT McFarland'

    This is from committee name 'Friends of Tyson Pratcher':
    >>> fec_crude_csv.read_filing(filing_230176_truncated,
    ...                           '230176.fec')['candidate']
    'Tyson Pratcher'

    This one is from an actual `candidate_name` field in form F6:
    >>> fec_crude_csv.read_filing(filing_230177_truncated,
    ...                           '230177.fec')['candidate']
    'Rick ODonnell'

    In this case there is a `candidate_name` field, but it is empty,
    because instead they used the `candidate_first_name`,
    `candidate_middle_name`, and `candidate_last_name` fields.  The
    `committee_name_(pcc)` field would give us 'Sue Kelly'.

    >>> fec_crude_csv.read_filing(filing_230179,
    ...                           '230179.fec')['candidate']
    'Sue W. Kelly'

    In this case, `candidate_name` contains a ^-separated name, which
    needs to be properly reordered.
    >>> fec_crude_csv.read_filing(filing_230185,
    ...                           '230179.fec')['candidate']
    'HOWARD KALOOGIAN'

    In this case, there is a more specific candidate name 'JOHN
    T. DOOLITTLE' to be extracted from the committee name, but we
    don’t yet do it.
    >>> fec_crude_csv.read_filing(filing_181904_truncated,
    ...                           '181904.fec')['candidate']
    'JOHN DOOLITTLE'

    """

filing_230174_truncated = '''HDR,FEC,5.3,CMDI FEC FILER,5.3.0,,FEC-211016,1,
F3A,C00415620,"KT McFarland for Congress","954 Lexington Avenue","Box 135","New York",NY,10021,,NY,14,Q1,P2006,20061101,NY,X,,,,20060101,20060331,172080.00,1000.00,171080.00,135651.09,0.00,135651.09,24293.78,0.00,0.00,168150.00,3930.00,172080.00,0.00,0.00,0.00,172080.00,0.00,0.00,0.00,0.00,0.00,0.00,172080.00,135651.09,400000.00,0.00,0.00,0.00,1000.00,0.00,0.00,1000.00,2000.00,538651.09,390864.87,172080.00,562944.87,538651.09,24293.78,602005.00,1000.00,601005.00,174691.47,0.00,174691.47,572075.00,3930.00,576005.00,0.00,1000.00,25000.00,602005.00,0.00,0.00,0.00,0.00,0.00,0.00,602005.00,174691.47,400000.00,0.00,0.00,0.00,1000.00,0.00,0.00,1000.00,2000.00,577691.47,"Alan McFarland",20060721,,,,,,,,,
SA11A1,C00415620,IND,,"219 East 69th Street","Apt 5-D","New York",NY,10021,P2006,,"Auda Private Equity LLC","Investment Manager",1000.00,20060201,1000.00,15,"Receipt",,,,,,,,,,,,,,,,60314.C590,,,,,,"Andryc","David",,,
SA11A1,C00415620,IND,,"219 East 69th Street","Apt 5-D","New York",NY,10021,P2006,,"Auda Private Equity LLC","Investment Manager",500.00,20060201,-500.00,15,"Reattribution Memo",,,,,,,,,,,,,X,"REATTRIBUTION TO SPOUSE",,60314.C591,60314.C590,SA11A1,,,,"Andryc","David",,,
'''

filing_230176_truncated = '''"HDR","FEC","5.3","NGP Campaign Office(R)","1.0e","","","0",""
"F3N","C00421578","Friends of Tyson Pratcher","454 North Willett","","Memphis","TN","38112","","TN","09","12P","P2006","20060803","TN","X","","","","20060401","20060714","3955.00","4200.00","-245.00","57578.74","171.00","57407.74","15078.20","0","0","2750.00","1205.00","3955.00","0","0","0","3955.00","0","0","0","0","171.00","0","4126.00","57578.74","0","0","0","0","0","0","4200.00","4200.00","5000.00","66778.74","77730.94","4126.00","81856.94","66778.74","15078.20","88064.44","4200.00","83864.44","63957.24","171.00","63786.24","76810.00","6054.44","82864.44","0","5200.00","0","88064.44","0","0","0","0","171.00","0","88235.44","63957.24","0","0","0","0","0","0","4200.00","4200.00","5000.00","73157.24","Horne^Allison","20060721","","","","","","","","",""
"SA11AI","C00421578","IND","","341 West 11th Street #8E","","New York","NY","10014","P2006","","Self-Employed","Attorney","500.00","20060519","500.00","","","","","","","","","","","","","","","","","","C350641","","","","","","Jones","Gregory","Davis","",""
'''

filing_230177_truncated = '''"HDR","FEC","5.3","Aristotle International CM4 PM4","Version 4.2.1","^","",""
"F6","C00374777","Coloradans for Rick ODonnell","PO Box 260693","","Lakewood","CO","80226   ","H2CO07055","Rick ODonnell","H","CO","07",20060721
"F65","C00374777","IND","ONeill^Timothy","2191 Baldy Lane","","Evergreen","CO","80439","Snell & Wilmer","Attorney",20060720,1000.00,"","","","","",,"","","","","","","","60721.C2980"
"F65","C00374777","IND","Kauffman^Kevin","K.P. Kauffman Company, In","1675 Broadway, Suite 28 ","Denver","CO","80202","K.P. Kauffman Company, In","Chairman, CEO",20060720,1600.00,"","","","","",,"","","","","","","","60721.C2977"
'''

filing_230179 = '''HDR,FEC,5.3,FILPAC,4.23,"^",,
F2N,H4NY19073,,187 Jay Street,,Katonah,NY,10536,REP,,NY,19,2006,C00294900,Sue Kelly for Congress,PO Box 599,,Katonah,NY,105360599,,ROMP IV 2006,"228 S. Washington St., Ste. 115",,Alexandria,VA,22314,Sue Kelly,20060721,0.00,0.00,Kelly,Sue,W.,,
'''

filing_230185 = '''HDR,FEC,5.3,FECfile,5.3.1.0(f16),,,
F1MN,C00400937,VETERANS FOR VICTORY PAC,"2245 148TH AVENUE, NE",,BELLEVUE,WA,98007,N,,,-,H4ND00038,SAND^DUANE^^,H,ND,00,20040810,H2CA39102,ESCOBAR^TIM^^,H,CA,39,20040817,H2KY04071,DAVIS^GEOFFREY C^^,H,KY,04,20040824,S6VT00111,PARKE^GREGORY TARL^^,S,VT,00,20041012,S4CA00282,KALOOGIAN^HOWARD^^,S,CA,00,20060329,20040617,20040510,20060329,MCCURDY^RUSSELL^^,20060722
'''

filing_181904_truncated = '''HDR,FEC,5.2,NetFile,1967,^,FEC-180228,001,Report Generated: 07/22/2005 11:18:27
F3A,C00242768,JOHN T. DOOLITTLE FOR CONGRESS,2150 RIVER PLAZA DR. #150,,SACRAMENTO,CA,95833,,CA,4,Q2,P2006,20060606,CA,,,,,20050401,20050630,151947.33,0.00,151947.33,99667.66,0.00,99667.66,215344.09,0.00,15468.80,105249.60,20172.73,125422.33,0.00,26525.00,0.00,151947.33,0.00,0.00,0.00,0.00,0.00,0.00,151947.33,99667.66,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,99667.66,163064.42,151947.33,315011.75,99667.66,215344.09,280515.83,0.00,280515.83,197866.25,3745.00,194121.25,182756.60,40384.23,223140.83,0.00,57375.00,0.00,280515.83,0.00,0.00,0.00,0.00,3745.00,0.00,284260.83,197866.25,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,27499.86,225366.11,David Bauer,20050722,H0CA14042,DOOLITTLE^JOHN,D31,259532.33,0.00,259532.33,5875.00,0.00,5875.00
SA11AI,C00242768,IND,,748 E. HILLCREST AVE.,,Yuba City,CA,95991,P2006,,,NONE,1200.00,20050417,1000.00,15,,,,,,,,,,,,,,,,,INC:A:63552,,,,,,BOYER,KARNA J.,,,
SA11AI,C00242768,IND,,2150 PROFESSIONAL DRIVE,,ROSEVILLE,CA,95661,P2006,,self,Property Management,350.00,20050417,350.00,15,,,,,,,,,,,,,,,,,INC:A:63536,,,,,,BRYANT,ERIC,,MR.,
'''

if __name__ == "__main__":
    cgitb.enable(format='text')
    doctest.testmod()
