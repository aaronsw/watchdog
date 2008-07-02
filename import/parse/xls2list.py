# MS Excel to Python list of list converter 
# 
# Provides the functions: 
# xls2list(fname, worksheet=1,encoding='cp1251') 
#  
# requires: 
# pyExcelerator 0.6.3a or later  
#  
 
from pyExcelerator import * 
from datetime import datetime 
 
def xls2list(fname, worksheet=1,encoding='cp1251'): 
    """  
    Return a Python list of lists that contains all cell-values  
    in the specified worksheet (default is the first)  
    of Excel spreadsheet with name=fname. 
     
    worksheet: an integer; worksheet=1 corresponds to the first  
    worksheet, etc. 
    encoding: use this unicode encoding, default is 'cp1251' 
     
    Interior blank cells are assigned the value None. 
     
    Example:  
    If the file "sales_beer.xls" consists of one worksheet with cells 
     
    "Year" "Sales" "Profit" 
    2001 1,000 300  
    2002 1,501 410 
    2003 1,900 520 
     
    Then the Python statement 
    sales=xls_to_list("sales_beer.xls) 
    will return the Python list object 
    sales=[["Year","Sales","Profit"], 
    [ 2001, 1000, 300], 
    [ 2002, 1501, 410], 
    [ 2003, 1900, 520]] 
     
    We assume a rectangular layout, and replace blank cells in the 
    spreadsheet with None values in the list.  
    The array dimensions is determined by the non-blank cells.  
     
    For example,  
    If the file "sales_cheap_beer.xls" contains one worksheet with cells 
     
    "Year" "Sales" "Profit" 
    2001 1,000 30  
    2002 1,501 41 
    2003 1,900 -52 blank "WHAT! NO PROFIT!!" 
     
    Then the Python statement 
    sales=xls_to_list("sales_cheap_beer.xls) 
    will return the Python rectangular list-of-lists object 
    sales=[["Year","Sales","Profit", None, None], 
    [ 2001, 1000, 30, None, None], 
    [ 2002, 1501, 41, None, None], 
    [ 2003, 1900, -52, None, "WHAT! NO PROFIT!!"]] 
     
     
    """ 
    data = parse_xls(fname,encoding) 
    # parse_xls returns a list of 2-tuples. One tuple for each worksheet. 
    # each tuple = (worksheet_name, worksheet_data) 
    # worksheet_data is a dict mapping each non-blank cell to its cell value. 
    # Each cell has a key of the form 
    # (i,j) with i=0,1,...,no_columns, j=0,1,...,no_rows 
    # to the associated cell entry. Blank cells are omitted from 
    # the dict. 
    sheet_name=data[worksheet-1][0]
    values = data[worksheet-1][1] 
     
    # first stuff all the nonempty cells into a dict keyed by tuples 
    # e.g. vdict[(0,0)] holds the contents of the top-left cell (if non-empty) 
    # else, (0,0) key will not exist in vdict. 
    # and vdict[(0,3)] corresponds to cell D1  
    # 0 -> row 1 (Excel row 1) and 3 -> column 4 (Excel column D) 
    vdict = {} 
    row_idx_max = 0 
    col_idx_max = 0 
    for row_idx, col_idx in sorted(values.keys()): 
        row_idx_max = max(row_idx,row_idx_max) 
        col_idx_max = max(col_idx,col_idx_max) 
        v = values[(row_idx, col_idx)] 
        vdict[(row_idx,col_idx)] = v 
     
    # Convert vdict (dict of cell values) to vlist (a 2D list). 
    # Blank cells are indicated by None. 
    vlist = [] 
    for row in range(row_idx_max+1): 
        vlist.append([]) 
        for col in range(col_idx_max+1): 
            if (row,col) not in vdict: 
                vdict[(row,col)]=None 
            vlist[row].append(vdict[(row,col)]) 
    return vlist 

