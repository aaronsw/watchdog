#!/usr/bin/python
# -*- coding: utf-8 -*-
import fec_crude_csv, doctest, cgitb
from cStringIO import StringIO

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

if __name__ == "__main__":
    cgitb.enable(format='text')
    doctest.testmod()
