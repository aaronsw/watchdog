"""
Parser for FEC Files for files that conform to webl.txt and weball.txt

Started 2008-04-16.
"""

__author__ = "Jeremy Schwartz <jerschwartz@gmail.com>"

import web

COBOL_INT_HASH = dict(']0 j1 k2 l3 m4 n5 o6 p7 q8 r9'.split())
def get_data_int(d):
    if not d or d[0] == '?':
        return d
    elif d[-1].lower() in COBOL_INT_HASH:
        d1 = d[:-1] + COBOL_INT_HASH[d[-1].lower()]
        return int(d1) * -1
    else:
        return int(d)

def get_data_str(d):
    return d.decode('cp1251').rstrip()

def get_data_date(d):
    return d[4:8] + "-" + d[0:2] + "-" + d[2:4]

PARTY_HASH = {"1": "Democratic", "2": "Republican", "3": "Other"}
def get_data_party(d):
    if d in PARTY_HASH:
        return PARTY_HASH[d]
    else:
        return get_data_str(d)

ICO_HASH = {" ": " ", "I": "Incumbent", "C": "Challenger", "O": "Open-Seat"}
def get_data_ico(d):
    if d in ICO_HASH:
        return ICO_HASH[d]
    else:
        return get_data_str(d)

def read_row(row, row_def):
    """Reads one row from data file and returns a list of columns."""
    out = web.storage()
    offset = 0
    for col in row_def:
        s = row[offset:offset + col[COL_LENGTH]]
        out[col[COL_NAME]] = col[COL_DATA](s)
        offset = offset + col[COL_LENGTH]
    return out

def read_fec_file(name, row_def):
    """Read an entire file."""
    for line in open(name):
        yield read_row(line, row_def)

COL_NAME = 0
COL_LENGTH = 1
COL_DATA = 2

# Row definition with field offset and names, conversion functions
WEB_ROW_DEF_SIZE = 243
WEB_ROW_DEF = [
  ("candidate_id",9,get_data_str),
  ("candidate_name",38,get_data_str),
  ("ico",1,get_data_ico),
  ("party",1,get_data_party),
  ("party_desig",3,get_data_str),
  ("total_receipts",10,get_data_int),
  ("auth_trans_from",10,get_data_int),
  ("total_disbursements",10,get_data_int),
  ("trans_to_auth",10,get_data_int),
  ("begin_cash",10,get_data_int),
  ("end_cash",10,get_data_int),
  ("contrib_from_candidate",10,get_data_int),
  ("loans_from_candidate",10,get_data_int),
  ("other_loans",10,get_data_int),
  ("candidate_loan_repay",10,get_data_int),
  ("other_loan_repay",10,get_data_int),
  ("debts_owed_by",10,get_data_int),
  ("total_indiv_contrib",10,get_data_int),
  ("state_code",2,get_data_str),
  ("district",2,get_data_str),
  ("spec_elec_status",1,get_data_str),
  ("primary_elec_status",1,get_data_str),
  ("runoff_elec_status",1,get_data_str),
  ("general_elec_status",1,get_data_str),
  ("general_elec_pct",3,get_data_str),
  ("contrib_from_other_pc",10,get_data_int),
  ("contrib_from_pc",10,get_data_int),
  ("end_date",8,get_data_date),
  ("refunds_to_indiv",10,get_data_int),
  ("refunds_to_commit",10,get_data_int)
]

# Supports files for CANSUM04 CANSUM02 CANSUM00 CANSUM98 CANSUM96
CANSUM_ROW_DEF = [
  ("candidate_id",9,get_data_str),
  ("candidate_name",38,get_data_str),
  ("ico",1,get_data_ico),
  ("party",1,get_data_party),
  ("party_desig",3,get_data_str),
  ("total_receipts",10,get_data_int),
  ("auth_trans_from",10,get_data_int),
  ("total_disbursments",10,get_data_int),
  ("trans_from_auth",10,get_data_int),
  ("begin_cash",10,get_data_int),
  ("end_cash",10,get_data_int),
  ("contrib_from_candidate",10,get_data_int),
  ("loans_from_candidate",10,get_data_int),
  ("other_loans",10,get_data_int),
  ("candidate_loan_repay",10,get_data_int),
  ("other_loan_repay",10,get_data_int),
  ("debts_owed_by",10,get_data_int),
  ("contrib_200_499",10,get_data_int),
  ("total_200_499",10,get_data_int),
  ("contrib_500_749",10,get_data_int),
  ("total_500_749",10,get_data_int),
  ("contrib_750",10,get_data_int),
  ("total_750",10,get_data_int),
  ("total_indiv_contrib",10,get_data_int),
  ("major_pty_contrib",10,get_data_int),
  ("party_indep_expend_for",10,get_data_int),
  ("corp_contrib",10,get_data_int),
  ("labor_contrib",10,get_data_int),
  ("non_connected_contrib",10,get_data_int),
  ("tmh_contrib",10,get_data_int),
  ("coop_contrib",10,get_data_int),
  ("corp_wo_stock_contrib",10,get_data_int),
  ("non_party_exp",10,get_data_int),
  ("non_party_exp_agn",10,get_data_int),
  ("indep_exp_for",10,get_data_int),
  ("indep_exp_agn",10,get_data_int),
  ("comm_cost_for",10,get_data_int),
  ("comm_cost_agn",10,get_data_int),
  ("state_code",2,get_data_str),
  ("district",2,get_data_str),
  ("spec_elec_status",1,get_data_str),
  ("primary_elec_status",1,get_data_str),
  ("runoff_elec_status",1,get_data_str),
  ("gen_elec_status",1,get_data_str),
  ("gen_elec_pct",7,get_data_int),
  ("spec_elec_cand",1,get_data_str),
  ("party_coord_exp",10,get_data_int),
  ("party_indep_exp",10,get_data_int)
]
CANSUM_ROW_DEF_SIZE = 419

# Supports format CANSUM94 CANSUM92
CANSUM_94_ROW_DEF = [
  ("candidate_id",9,get_data_str),
  ("candidate_name",38,get_data_str),
  ("ico",1,get_data_ico),
  ("party",1,get_data_party),
  ("party_desig",3,get_data_str),
  ("total_reciepts",10,get_data_int),
  ("auth_trans_from",10,get_data_int),
  ("total_disbursments",10,get_data_int),
  ("trans_to_auth",10,get_data_int),
  ("begin_cash",10,get_data_int),
  ("end_cash",10,get_data_int),
  ("contrib_from_cand",10,get_data_int),
  ("loans_from_cand",10,get_data_int),
  ("other_loans",10,get_data_int),
  ("cand_loans_repay",10,get_data_int),
  ("other_loan_repay",10,get_data_int),
  ("debts_owned_by",10,get_data_int),
  ("contrib_200_499",10,get_data_int),
  ("total_200_499",10,get_data_int),
  ("contrib_500_749",10,get_data_int),
  ("total_500_749",10,get_data_int),
  ("contrib_750",10,get_data_int),
  ("total_750",10,get_data_int),
  ("total_indiv_contrib",10,get_data_int),
  ("major_pty_contrib",10,get_data_int),
  ("pty_coord_expend",10,get_data_int),
  ("corp_contrib",10,get_data_int),
  ("labor_contrib",10,get_data_int),
  ("non_connect_cont",10,get_data_int),
  ("tmh_contrib",10,get_data_int),
  ("coop_contrib",10,get_data_int),
  ("corp_wo_stock",10,get_data_int),
  ("non_party_exp",10,get_data_int),
  ("non_party_exp_agn",10,get_data_int),
  ("indep_exp_for",10,get_data_int),
  ("indep_exp_agn",10,get_data_int),
  ("comm_cost_for",10,get_data_int),
  ("comm_cost_agn",10,get_data_int),
  ("state_code",2,get_data_str),
  ("district",2,get_data_str),
  ("spec_elec_status",1,get_data_str),
  ("primary_elec_status",1,get_data_str),
  ("runoff_elec_status",1,get_data_str),
  ("gen_elec_status",7,get_data_str),
  ("spec_elec_cand",1,get_data_str)
]
CANSUM_94_ROW_DEF_SIZE = 402


CANSUM_90_ROW_DEF = [
  ("candidate_id",9,get_data_str),
  ("candidate_name",38,get_data_str),
  ("ico",1,get_data_ico),
  ("fill",10,get_data_str),
  ("party",1,get_data_party),
  ("party_desig",3,get_data_str),
  ("total_reciepts",12,get_data_int),
  ("auth_trans_from",12,get_data_int),
  ("total_disbursments",12,get_data_int),
  ("trans_to_auth",12,get_data_int), #9
  ("begin_cash",12,get_data_int),
  ("end_cash",12,get_data_int),
  ("contrib_from_cand",12,get_data_int),
  ("loans_from_cand",12,get_data_int),
  ("other_loans",12,get_data_int),
  ("cand_loans_repay",12,get_data_int),
  ("other_loan_repay",12,get_data_int),
  ("debts_owned_by",12,get_data_int),
  ("contrib_200_499",8,get_data_int),
  ("total_200_499",12,get_data_int), #19
  ("contrib_500_749",8,get_data_int),
  ("total_500_749",12,get_data_int),
  ("contrib_750",8,get_data_int),
  ("total_750",12,get_data_int),
  ("total_indiv_contrib",12,get_data_int),
  ("major_pty_contrib",12,get_data_int),
  ("pty_coord_expend",12,get_data_int),
  ("corp_contrib",12,get_data_int),
  ("labor_contrib",12,get_data_int),
  ("non_connect_cont",12,get_data_int), #29
  ("tmh_contrib",12,get_data_int), #30
  ("coop_contrib",12,get_data_int),
  ("corp_wo_stock",12,get_data_int),
  ("non_party_exp",12,get_data_int),
  ("non_party_exp_agn",12,get_data_int),
  ("indep_exp_for",12,get_data_int),
  ("indep_exp_agn",12,get_data_int),
  ("comm_cost_for",12,get_data_int),
  ("comm_cost_agn",12,get_data_int), #38
  ("state_code",2,get_data_str),
  ("district",2,get_data_str),
  ("spec_elec_status",1,get_data_str),
  ("primary_elec_status",1,get_data_str),
  ("runoff_elec_status",1,get_data_str),
  ("gen_elec_status",1,get_data_str),
  ("spec_elec_cand",1,get_data_str)
]
CANSUM_90_ROW_DEF_SIZE = 461

CANSUM_88_ROW_DEF = [
  ("candidate_id",9,get_data_str),
  ("candidate_name",38,get_data_str),
  ("ico",1,get_data_ico),
  ("fill",10,get_data_str),
  ("party",1,get_data_party),
  ("party_desig",3,get_data_str),
  ("total_reciepts",12,get_data_int),
  ("auth_trans_from",12,get_data_int),
  ("total_disbursments",12,get_data_int),
  ("trans_to_auth",12,get_data_int), #9
  ("begin_cash",12,get_data_int),
  ("end_cash",12,get_data_int),
  ("contrib_from_cand",12,get_data_int),
  ("loans_from_cand",12,get_data_int),
  ("other_loans",12,get_data_int),
  ("cand_loans_repay",12,get_data_int),
  ("other_loan_repay",12,get_data_int),
  ("debts_owned_by",12,get_data_int),
  ("contrib_500_749",8,get_data_int),
  ("total_500_749",12,get_data_int),
  ("contrib_750",8,get_data_int),#20
  ("total_750",12,get_data_int),
  ("total_indiv_contrib",12,get_data_int),
  ("major_pty_contrib",12,get_data_int),
  ("pty_coord_expend",12,get_data_int),
  ("corp_contrib",12,get_data_int),
  ("labor_contrib",12,get_data_int),
  ("non_connect_cont",12,get_data_int), 
  ("tmh_contrib",12,get_data_int), 
  ("coop_contrib",12,get_data_int),
  ("corp_wo_stock",12,get_data_int),#30
  ("non_party_exp",12,get_data_int),
  ("non_party_exp_agn",12,get_data_int),
  ("indep_exp_for",12,get_data_int),
  ("indep_exp_agn",12,get_data_int),
  ("comm_cost_for",12,get_data_int),
  ("comm_cost_agn",12,get_data_int), 
  ("state_code",2,get_data_str),
  ("district",2,get_data_str),
  ("spec_elec_status",1,get_data_str),
  ("primary_elec_status",1,get_data_str),
  ("runoff_elec_status",1,get_data_str),
  ("gen_elec_status",1,get_data_str),
  ("spec_elec_cand",1,get_data_str)
]
CANSUM_88_ROW_DEF_SIZE = 440

PAS2_DEF = [
  ("from_committee_id", 9, get_data_str),
  ("amendment_status", 1, get_data_str), #@@enumeration
  ("report_type", 3, get_data_str), #@@enumeration
  ("primary_general", 1, get_data_str), #@@enumeration
  ("microfilm_loc", 11, get_data_str),
  ("type", 3, get_data_str), #@@@@ important enumeration
  ("date", 8, get_data_date),
  ("amount", 7, get_data_int),
  ("to_other_id", 9, get_data_str),
  ("to_candidate_id", 9, get_data_str),
  ("fec_record_id", 7, get_data_str)
]

CM_DEF = [
  ("committee_id", 9, get_data_str),
  ("committee_name", 90, get_data_str),
  ("treasurer_name", 38, get_data_str),
  ("street_one", 34, get_data_str),
  ("street_two", 34, get_data_str),
  ("city", 18, get_data_str),
  ("state", 2, get_data_str),
  ("zip", 5, get_data_str),
  ("committee_designation", 1, get_data_str), #@@enumeration
  ("committee_type", 1, get_data_str), #@@enumeration
  ("committee_party", 3, get_data_str), #@@enumeration
  ("filing_frequency", 1, get_data_str), #@@enumeration
  ("interest_group_category", 1, get_data_str), #@@@@important enumeration
  ("connected_org_name", 38, get_data_str),
  ("candidate_id", 9, get_data_str)
]


def parse_candidates():
    return read_fec_file("../data/crawl/fec/2008/weball.dat", WEB_ROW_DEF)
def parse_committees():
    return read_fec_file("../data/crawl/fec/2008/cm.dat", CM_DEF)
def parse_transfers():
    return read_fec_file("../data/crawl/fec/2008/pas2.dat", PAS2_DEF)

if __name__ == "__main__":
    import tools
    tools.export(parse_candidates())
    tools.export(parse_committees())
    tools.export(parse_transfers())

#result = read_fec_file("WEBL08.DAT",WEB_ROW_DEF,WEB_ROW_DEF_SIZE)
#result = read_fec_file("cansum04.txt",CANSUM_ROW_DEF,CANSUM_ROW_DEF_SIZE)
#result = read_fec_file("CANSUM94.DAT",CANSUM_94_ROW_DEF,CANSUM_94_ROW_DEF_SIZE)
#result = read_fec_file("CANSUM90.DAT",CANSUM_90_ROW_DEF,CANSUM_90_ROW_DEF_SIZE)
#result = read_fec_file("cansum88.dat",CANSUM_88_ROW_DEF,CANSUM_88_ROW_DEF_SIZE)
#print result
