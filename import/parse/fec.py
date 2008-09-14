"""
Parser for FEC Files for files that conform to webl.txt and weball.txt

Parser for FEC electronic filings

Started 2008-04-16.
"""

__author__ = [
  "Jeremy Schwartz <jerschwartz@gmail.com>",
  "Aaron Swartz <me@aaronsw.com>",
  "Simon Carstensen <me@simonbc.com>"
]

import gzip
import zipfile
import web
import re
import os
import sys

COBOL_INT_TABLE = dict(']0 j1 k2 l3 m4 n5 o6 p7 q8 r9'.split())
def get_data_int(d):
    if not d or d[0] == '?':
        return d
    elif d[-1].lower() in COBOL_INT_TABLE:
        d1 = d[:-1] + COBOL_INT_TABLE[d[-1].lower()]
        return -int(d1)
    elif d[0] == '+':
        return int(d[1:])
    elif d[0] == "-":
        return -int(d[1:])
    else:
        return int(d)

def get_data_str(d):
    return d.decode('cp1251').rstrip()

def get_data_date(d):
    "MMDDYYYY"
    return d[4:8] + "-" + d[0:2] + "-" + d[2:4]

def get_data_date2(d):
    "??DDMMYYYY"
    return d[6:10] + "-" + d[4:6] + "-" + d[2:4]

def table_lookup(table):
    def get_from_table(d):
        if d in table:
            return table[d]
        else:
            return get_data_str(d)
    return get_from_table

get_data_party = table_lookup({
  "1": "Democratic",
  "2": "Republican",
  "3": "Other"
})

get_data_ico = table_lookup({
  " ": " ",
  "I": "Incumbent",
  "C": "Challenger",
  "O": "Open-Seat"
})

get_ff_type = table_lookup({ # filing frequency
    'M': "Monthly",
    'Q': "Quarterly",
    "T": "Terminated"
})

get_comte_type = table_lookup({
    'C': "COMMUNICATION COST",
    'D': "DELEGATE",
    'H': "HOUSE",
    'I': "INDEPENDENT EXPENDITURE (PERSON OR GROUP, NOT A COMMITTEE)",
    'N': "NON-PARTY NON-QUALIFIED",
    'P': "PRESIDENTIAL",
    'Q': "QUALIFIED NON-PARTY (SEE 2 USC 441(A)(4))",
    'S': "SENATE",
    'X': "NON-QUALIFIED PARTY",
    'Y': "QUALIFIED PARTY (SEE 2 USC 441(A)(4))",
    'Z': "NATIONAL PARTY ORGANIZATION. NON FED ACCT."
})

get_comte_desig = table_lookup({
   'A': "AUTHORIZED BY A CANDIDATE",
   'J': "JOINT FUND RAISER",
   'P': "PRINCIPAL CAMPAIGN COMMITTEE OF A CANDIDATE",
   'U': "UNAUTHORIZED"
})

def read_row(row, row_def):
    """Reads one row from data file and returns a list of columns."""
    out = web.storage()
    offset = 0
    for col in row_def:
        s = row[offset:offset + col[COL_LENGTH]]
        out[col[COL_NAME]] = col[COL_DATA](s)
        offset = offset + col[COL_LENGTH]
    return out

def read_fec_file(fh, row_def):
    """Read an entire file."""
    for line in fh:
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

WEBK_ROW_DEF = [
    ("id",9,get_data_str),
    ("name",90,get_data_str),
    ("type",1,get_comte_type),
    ("desig",1,get_comte_desig),
    ("ff",1,get_ff_type),
    ("total_receipts",10,get_data_int),
    ("trans_from_aff",10,get_data_str),
    ("contrib_rec_from_indiv",10,get_data_int),
    ("contrib_rec_from_other_pc",10,get_data_int),
    ("contrib_from_cand",10,get_data_int),
    ("cand_loans",10,get_data_int),
    ("total_loans_rec",10,get_data_int),
    ("total_disbursment",10,get_data_int),
    ("trans_to_aff",10,get_data_int),
    ("refunds_to_indiv",10,get_data_int),
    ("refunds_to_other_pc",10,get_data_int),
    ("cand_loan_repayments",10,get_data_int),
    ("loan_repayments",10,get_data_int),
    ("cash_begin",10,get_data_int),
    ("cash_close",10,get_data_int),
    ("debts_bowned_by",10,get_data_int),
    ("nonfederal_trans_rec",10,get_data_int),
    ("contrib_made_to_other",10,get_data_int),
    ("indep_exped_made",10,get_data_str),
    ("party_coord_expend_made",10,get_data_int),
    ("nonfederal_share_of_expend",10,get_data_int),
    ("month",2,get_data_int),
    ("day",2,get_data_int),
    ("year",4,get_data_int)
]
#Supporst PACSUM[92-04]
PAC_SUM_ROW_DEF = [
    ("committee_id",9,get_data_str),
    ("committee_name",90,get_data_str),
    ("sig",1,get_data_str),
    ("end_coverage_date",6,get_data_date),
    ("total_receipts",10,get_data_int),
    ("trans_from_aff",10,get_data_int),
    ("contrib_from_party",10,get_data_int),
    ("contrib_from_non_party",10,get_data_int),
    ("total_indiv_contrib",10,get_data_int),
    ("indiv_contrib_200+",10,get_data_int),
    ("in_kind_contrib",10,get_data_int),
    ("total_disbursements",10,get_data_int),
    ("trans_to_aff",10,get_data_int),
    ("contrib_to_party",10,get_data_int),
    ("contrib_to_non_party",10,get_data_int),
    ("indiv_contrib_refund",10,get_data_int),
    ("begin_cash",10,get_data_int),
    ("end_cash",10,get_data_int),
    ("debts_owed_to",10,get_data_int),
    ("debts_owed_by",10,get_data_int),
    ("total_in_kind_contrib",10,get_data_int),
    ("total_1999_contrib",10,get_data_int),
    ("total_for",10,get_data_int),
    ("total_against",10,get_data_int),
    ("pres_contrib_dem",10,get_data_int),
    ("pres_contrib_rep",10,get_data_int),
    ("pres_contrib_oth",10,get_data_int),
    ("senate_contrib_dem",10,get_data_int),
    ("senate_contrib_rep",10,get_data_int),
    ("senate_contrib_oth",10,get_data_int),
    ("house_contrib_dem",10,get_data_int),
    ("house_contrib_rep",10,get_data_int),
    ("house_contrib_oth",10,get_data_int),
    ("senate_inc_contrib",10,get_data_int),
    ("senate_cha_contrib",10,get_data_int),
    ("senate_opn_contrib",10,get_data_int),
    ("house_inc_contrib",10,get_data_int),
    ("house_cha_contrib",10,get_data_int),
    ("house_opn_contrib",10,get_data_int),
    ("non_federal_trans",10,get_data_int),
    ("non_federal_expend",10,get_data_int)]


#Supporst PACSUM[84-90]
PAC_SUM_90_ROW_DEF = [
    ("committee_id",9,get_data_str),
    ("committee_name",90,get_data_str),
    ("sig",1,get_data_str),
    ("end_coverage_date",10,get_data_date2),
    ("total_receipts",12,get_data_int),
    ("contrib_from_aff",12,get_data_int),
    ("contrib_from_party",12,get_data_int),
    ("contrib_from_non_party",12,get_data_int),
    ("indiv_contrib",12,get_data_int),
    ("total_contrib",12,get_data_int),
    ("in_kind_contrib",12,get_data_int),
    ("total_disbursements",12,get_data_int),
    ("contrib_to_non_party_aff",12,get_data_int),
    ("contrib_to_party",12,get_data_int),
    ("contrib_to_non_party",12,get_data_int),
    ("indiv_contrib_refund",12,get_data_int),
    ("begin_cash_year_1",12,get_data_int),
    ("end_cash_year_2",12,get_data_int),
    ("debts_owed_to",12,get_data_int),
    ("debts_owed_by",12,get_data_int),
    ("total_in_kind_contrib",12,get_data_int),
    ("total_1_contrib",12,get_data_int),
    ("total_indep_for",12,get_data_int),
    ("total_indep_against",12,get_data_int),
    ("pres_contrib_dem",12,get_data_int),
    ("pres_contrib_rep",12,get_data_int),
    ("pres_contrib_oth",12,get_data_int),
    ("senate_contrib_dem",12,get_data_int),
    ("senate_contrib_rep",12,get_data_int),
    ("senate_contrib_oth",12,get_data_int),
    ("house_contrib_dem",12,get_data_int),
    ("house_contrib_rep",12,get_data_int),
    ("house_contrib_oth",12,get_data_int),
    ("senate_inc_contrib",12,get_data_int),
    ("senate_cha_contrib",12,get_data_int),
    ("senate_opn_contrib",12,get_data_int),
    ("house_inc_contrib",12,get_data_int),
    ("house_cha_contrib",12,get_data_int),
    ("house_opn_contrib",12,get_data_int)]


#Supporst PACSUM[80-82]
PAC_SUM_82_ROW_DEF = [
    ("committee_id",9,get_data_str),
    ("committee_name",90,get_data_str),
    ("committee_type",1,get_data_str),
    ("sig",1,get_data_str),
    ("party",3,get_data_str),
    ("not_used",1,get_data_str),
    ("state",2,get_data_str),
    ("total_receipts",10,get_data_int),
    ("trans_in_party",10,get_data_int),
    ("trans_in_party_other",10,get_data_int),
    ("corp_contrib",10,get_data_int),
    ("labor_contrib",10,get_data_int),
    ("non_connected_contrib",10,get_data_int),
    ("tmh_contrib",10,get_data_int),
    ("coop_contrib",10,get_data_int),
    ("corp_wo_stock_contrib",10,get_data_int),
    ("num_cand_contrib_to",10,get_data_int),
    ("total_party_contrib",10,get_data_int),
    ("not_used2",10,get_data_str),
    ("not_used3",10,get_data_str),
    ("contrib_500+",10,get_data_int),
    ("total_disbursements",10,get_data_int),
    ("trans_out_party_same",10,get_data_int),
    ("trans_out_party_other",10,get_data_int),
    ("total_contrib",10,get_data_int),
    ("not_used4",80,get_data_str),
    ("latest_cash_on_hand",10,get_data_int),
    ("jan_1_cash_on_hand",10,get_data_int),
    ("debts_owed_to",10,get_data_int),
    ("debts_owed_by",10,get_data_int),
    ("in_kind_contrib",10,get_data_int),
    ("contrib_refunds",10,get_data_int),
    ("contrib_to_dem_pres",10,get_data_int),
    ("contrib_to_rep_pres",10,get_data_int),
    ("contrib_to_other_pres",10,get_data_int),
    ("contrib_to_dem_senate",10,get_data_int),
    ("contrib_to_rep_senate",10,get_data_int),
    ("contrib_to_other_senate",10,get_data_int),
    ("contrib_to_dem_house",10,get_data_int),
    ("contrib_to_rep_house",10,get_data_int),
    ("contrib_to_other_house",10,get_data_int),
    ("expend_on_dem_pres",10,get_data_int),
    ("expend_on_rep_pres",10,get_data_int),
    ("expend_on_other_pres",10,get_data_int),
    ("expend_on_dem_senate",10,get_data_int),
    ("expend_on_rep_senate",10,get_data_int),
    ("expend_on_other_senate",10,get_data_int),
    ("expend_on_dem_house",10,get_data_int),
    ("expend_on_rep_house",10,get_data_int),
    ("expend_on_other_house",10,get_data_int),
    ("end_coverage_date",8,get_data_date),
    ("senate_house_inc_contrib",9,get_data_int),
    ("senate_house_cha_contrib",9,get_data_int),
    ("senate_house_opn_contrib",9,get_data_int)]

INDIV_ROW_DEF = [
  ('filer_id', 9, get_data_str),
  ('amendment_type', 1, get_data_str), #@@enumeration
  ('report_type', 3, get_data_str), #@@enumeration
  ('primary_general', 1, get_data_str), #@@enumeration
  ('microfilm_loc', 11, get_data_str),
  ('transaction_type', 3, get_data_str), #@@important enumeration
  ('src_name', 34, get_data_str),
  ('src_city', 18, get_data_str),
  ('src_state', 2, get_data_str),
  ('src_zip', 5, get_data_str),
  ('src_occupation', 35, get_data_str),
  ('date', 8, get_data_date),
  ('amount', 7, get_data_int),
  ('src_id', 9, get_data_str),
  ('fec_record_id', 7, get_data_str)
]

def parse_candidates():
    return read_fec_file(file("../data/crawl/fec/2008/weball.dat"), WEB_ROW_DEF)
def parse_committees():
    return read_fec_file(file("../data/crawl/fec/2008/cm.dat"), CM_DEF)
def parse_transfers():
    return read_fec_file(file("../data/crawl/fec/2008/pas2.dat"), PAS2_DEF)
def parse_contributions():
    return read_fec_file(gzip.open("../data/crawl/fec/2008/indiv.dat.gz"), INDIV_ROW_DEF)

HEADERS_PATH = '../data/crawl/fec/electronic/headers/'
def parse_headers():
    """Parse and load the specifications of the FEC electronic filing formats"""

    files = os.listdir(HEADERS_PATH)
    files.sort()
    out = dict()
    for f in filter(lambda x: x.endswith('.csv'), files):
        headers = file(HEADERS_PATH+f).read().strip()
        headers = headers.split('\r') # split into lines
        headers = filter(lambda x: not x.startswith('TEXT'), headers) # remove comments
        ver = f[:-4]
        out[ver] = dict()
        for h in headers:
            cols = map(lambda x: x.strip(), h.split(';'))
            cols = filter(lambda x: x != '', cols)
            form_type = cols[0].replace(' ', '')
            out[ver][form_type] = cols[1:]
    return out

def value_separator(header):
    """Determine whether the value separator is "," or FS"""
    if header.startswith('/* Header'):
        # we don't know how to parse format verison 2.0
        return None
    comma_separated = header.startswith('HDR,') or header.startswith('"HDR",')
    return comma_separated and ',' or chr(28)

def fixquotes(val):
    """Sometimes values are put inside quotes, remove these"""
    if val.startswith('"') and val.endswith('"'):
        val = val[1:]
        val = val[:-1]
    return val

VERSIONS = ['3.00', '5.00', '5.1', '5.2', '6.1', '6.2']
def get_format_ver(hdr, sep):
    """Determines the format version of a given FEC file"""
    ver = hdr.split(sep)[2]
    ver = fixquotes(ver)
    ver = ver.strip()
    return (ver in VERSIONS and ver) or None

def get_form_type(report, sep, ver):
    type = report.split(sep)[0]
    type = fixquotes(type)
    return type

def get_orig_report_id(hdr, sep, ver):
    i = (ver in ['6.1', '6.2'] and 5) or 6
    out = fixquotes(hdr.split(sep)[i])[4:]
    return out

def get_report_no(hdr, sep, ver):
    i = (ver in ['6.1', '6.2'] and 6) or 7
    out = fixquotes(hdr.split(sep)[i])
    return out

SPLIT_RE = re.compile('(,"[^,"]+),([^,"])')
def rsplit(filing, sep):
    """split for FEC records"""
    if sep == ',':
        # make sure we don't split inside quotes
        n = 1
        while n:
            filing, n = SPLIT_RE.subn('\g<1>\x1c\g<2>', filing)
        out = filing.split(',')
        out = [o.replace(chr(28), ',') for o in out]
    else:
        out = filing.split(sep)
        if not out[-1]:
            out = out[:-1]
    out = [fixquotes(o) for o in out]
    return out

def amendment_sort(x, y):
    return cmp(x['report_no'], y['report_no'])

EFILINGS_PATH = '../data/crawl/fec/electronic/'
def file_index():
    files = os.listdir(EFILINGS_PATH)
    zfiles = filter(lambda f: f.endswith('.zip'), files)
    reports = list()
    amendments = dict()
    for f in zfiles:
        print >> sys.stderr, '\r', f,
        sys.stderr.flush()
        if not os.stat(EFILINGS_PATH+f).st_size: continue
        zf = zipfile.ZipFile(EFILINGS_PATH+f)
        filenames = zf.namelist()
        for fn in filenames:
            d = read_report(f, fn, zf.read(fn))
            if not d:
                continue
            if d['form_type'].endswith('A'):
                # amendment
                orig_report_id = get_orig_report_id(d['hdr'], d['sep'], d['ver'])
                d['report_no'] = get_report_no(d['hdr'], d['sep'], d['ver'])
                if not amendments.has_key(orig_report_id):
                    amendments[orig_report_id] = list()
                amendments[orig_report_id].append(d)
            else:
                # new report or termination
                reports.append(d)
        zf.close()
    for k, v in amendments.items():
        amendments[k] = sorted(v, amendment_sort)
    return (reports, amendments)

def get_form_id(report, sep):
    return rsplit(report, sep)[1]

def get_committee(report, sep):
    return rsplit(report, sep)[2]

def get_candidate_fec(header, report, form_type, ver):
    if form_type.startswith('F3X'):
        return None
    if ver in ['6.1', '6.2']:
        i = header.index('CANDIDATE ID NUMBER')
    else:
        i = header.index('FEC CANDIDATE ID NUMBER')
    if len(report) <= i: return None
    out = report[i].strip() or None
    return out

def get_contrib_candidate_fec(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('DONOR CANDIDATE FEC ID')
    else:
        i = header.index('FEC CANDIDATE ID NUMBER')
    if len(schedule) <= i: return None
    out = schedule[i] or None
    return out

def get_expend_candidate_fec(header, schedule, ver):
    if ver == '6.1':
        i = header.index('PAYEE CANDIDATE FEC ID')
    elif ver == '6.2':
        i = header.index('BENEFICIARY CANDIDATE FEC ID')
    else:
        i = header.index('FEC CANDIDATE ID NUMBER')
    if len(schedule) <= i: return None
    out = schedule[i] or None
    return out

RE_COMMITTEE = re.compile('([^ ]+ .+) for congress', re.IGNORECASE)
def get_candidate(header, report, form_type, sep, ver):
    fields = rsplit(report, sep)
    if form_type.startswith('F3X'):
        return None
    if ver in ['6.1', '6.2']:
        i_first = header.index('CANDIDATE FIRST NAME')
        i_middle = header.index('CANDIDATE MIDDLE NAME')
        i_last = header.index('CANDIDATE LAST NAME')
        if len(fields) <= i_middle: return None
        middle = fields[i_middle]
        middle = middle + (len(middle) is 1 and '.' or '')
        out = ' '.join(filter(lambda x: x, [fields[i_first], middle, fields[i_last]]))
    else:
        i = header.index('11(d) The Candidate')
        if len(fields) <= i: return None
        out = fields[i]
    if not out:
        #committee name is sometimes 'x for Congress', get candidate name here
        committee = get_committee(report, sep)
        m =  RE_COMMITTEE.match(committee)
        if m:
            out = m.groups()[0]
    return out or None

def get_tran_id(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('TRANSACTION ID NUMBER')
    else:
        i = header.index('TRAN ID')
    if len(schedule) <= i: return None
    out = schedule[i] or None
    return out

def get_occupation(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('CONTRIBUTOR OCCUPATION')
        if len(schedule) <= i: return None
        return schedule[i] or None
    else:
        return None

def get_contributor_org(header, schedule, ver):
    if ver in ['3.00', '5.0']:
        return None
    if ver in ['6.1', '6.2']:
        i = header.index('CONTRIBUTOR ORGANIZATION NAME')
    else:
        i = header.index('CONTRIB ORGANIZATION NAME')

    if len(schedule) <= i: return None
    return schedule[i] or None

def get_contributor(header, sch, ver):
    if ver in ['6.1', '6.2']:
        i_first = header.index('CONTRIBUTOR FIRST NAME')
        i_middle = header.index('CONTRIBUTOR MIDDLE NAME')
        i_last = header.index('CONTRIBUTOR LAST NAME')
        if len(sch) <= i_middle: return None
        middle = sch[i_middle]
        middle = middle + (len(middle) is 1 and '.' or '')
        out = ' '.join(filter(lambda x: x, [sch[i_first], middle, sch[i_last]]))
    else:
        i = header.index('CONTRIBUTOR NAME')
        if len(sch) <= i: return None
        out = sch[i]
    return out or None

def get_employer(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('CONTRIBUTOR EMPLOYER')
        if len(schedule) <= i: return None
        return schedule[i] or None
    else:
        return None

def get_contribution_amount(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('CONTRIBUTION AMOUNT')
    else:
        i = header.index('AMOUNT RECEIVED')
    if len(schedule) <= i: return None
    return schedule[i] or None

def get_expenditure_amount(header, schedule, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('EXPENDITURE AMOUNT')
    else:
        i = header.index('AMOUNT OF EXPENDITURE')
    if len(schedule) <= i: return None
    return schedule[i] or None

def get_recipient(header, sch, ver):
    if ver in ['6.1', '6.2']:
        i = header.index('PAYEE ORGANIZATION NAME')
    else:
        i = header.index('RECIPIENT NAME')
    if len(sch) <= i: return None
    out = sch[i]
    return out.strip() or None

def get_contribution_date(header, sch, ver):
    "YYYYMMDD"
    if ver in ['6.1', '6.2']:
        i = header.index('CONTRIBUTION DATE')
    else:
        i = header.index('DATE RECEIVED')
    if len(sch) <= i: return None
    date = sch[i]
    if not date:
        return None
    year = date[0:4]
    month = date[4:6]
    day = date[6:8]
    return '%s-%s-%s' % (year, month, day)

def get_expenditure_date(header, sch, ver):
    "YYYYMMDD"
    if ver in ['6.1', '6.2']:
        i = header.index('EXPENDITURE DATE')
    else:
        i = header.index('DATE OF EXPENDITURE')
    if len(sch) <= i: return None
    date = sch[i]
    if not date:
        return None
    year = date[0:4]
    month = date[4:6]
    day = date[6:8]
    return '%s-%s-%s' % (year, month, day)

def get_header(headers, form_type, ver):
    if not headers.has_key(ver): return None
    headers = headers[ver]
    if form_type.startswith('F'):
        form_type = form_type[:-1] # remove 'N', 'T' or 'A'
    elif form_type.startswith('S'):
        if ver in ['5.2', '6.1', '6.2']:
            form_type = 'Sch'+form_type[1]
        else:
            form_type = 'S'+form_type[1]
    return headers.has_key(form_type) and headers[form_type] or None

SCH_RE = re.compile('^"?(Sch|S)(A|B)')
SCHA_RE = re.compile('^(Sch|S)A')
def get_schedules(headers, schedules, sep, ver):
    out = dict()
    for s in schedules:
        if not SCH_RE.match(s):
            continue
        sch = dict()
        sch['form_type'] = get_form_type(s, sep, ver)
        header = get_header(headers, sch['form_type'], ver)
        if not header:
            continue
        fields = rsplit(s, sep)
        sch['tran_id'] = get_tran_id(header, fields, ver)
        if SCHA_RE.match(sch['form_type']):
            sch['type'] = 'contribution'
            sch['date'] = get_contribution_date(header, fields, ver)
            sch['contributor_org'] = get_contributor_org(header, fields, ver)
            sch['contributor'] = get_contributor(header, fields, ver)
            sch['occupation'] = get_occupation(header, fields, ver)
            sch['employer'] = get_employer(header, fields, ver)
            sch['amount'] = get_contribution_amount(header, fields, ver)
        else:
            sch['type'] = 'expenditure'
            sch['date'] = get_expenditure_date(header, fields, ver)
            sch['recipient'] = get_recipient(header, fields, ver)
            sch['amount'] = get_expenditure_amount(header, fields, ver)
        out[sch['tran_id']] = sch
    return out

def get_records(data):
    zf = zipfile.ZipFile(EFILINGS_PATH+data['zfn'])
    filing = zf.read(data['report_id']+'.fec')
    lines = filing.split('\n')
    lines = filter(lambda x: x != '', map(lambda x: x.strip(), lines))
    lines = map(lambda x: x.decode('latin1'), lines)
    cover, schedules = lines[1], lines[2:]
    return cover, schedules

def get_report(headers, data):
    cover, schedules = get_records(data)
    form_type, ver, sep = data['form_type'], data['ver'], data['sep']
    header = get_header(headers, form_type, ver)
    out = dict()
    out['filer_id'] = get_form_id(cover, sep)
    out['form_type'] = form_type
    out['report_id'] = data['report_id']
    out['committee'] = get_committee(cover, sep)
    out['candidate'] = get_candidate(header, cover, form_type, sep, ver)
    out['candidate_fec_id'] = get_candidate_fec(header, cover, form_type, ver)
    out['schedules'] = get_schedules(headers, schedules, sep, ver)
    return out

FORM_TYPES = ['F3', 'F3N', 'F3A', 'F3T', 'F3X', 'F3XN', 'F3XA', 'F3T']
def read_report(zfilename, filename, data):
    report_id = filename[:-4]
    lines = data.split('\n')
    lines = filter(lambda x: x != '', map(lambda x: x.strip(), lines))
    lines = map(lambda x: x.decode('latin1'), lines)
    hdr, records = lines[0], lines[1:]
    sep = value_separator(hdr)
    if not sep:
        return None
    ver = get_format_ver(hdr, sep)
    if not ver:
        return None
    form_type = get_form_type(records[0], sep, ver)
    if form_type not in FORM_TYPES:
        return None
    out = dict(zfn=zfilename, report_id=report_id, hdr=hdr, sep=sep, ver=ver, form_type=form_type)
    return out

def apply_amendment(headers, report, amendment):
    cover, schedules = get_records(amendment)
    sep, ver = amendment['sep'], amendment['ver']
    amendment = get_report(headers, amendment)
    report['committee'] = amendment['committee']
    report['candidate'] = amendment['candidate']
    for k, v in amendment['schedules'].items():
        report['schedules'][k] = v

def apply_amendments(headers, report, amendments):
    report_id = report['report_id']
    if amendments.has_key(report_id):
        amendments = amendments[report_id]
        for a in amendments:
            apply_amendment(headers, report, a)
    report['schedules'] = report['schedules'].values()
    return report

def get_filings(headers, reports, amendments):
    for r in reports:
        r = get_report(headers, r)
        r = apply_amendments(headers, r, amendments)
        yield r

def parse_efilings():
    headers = parse_headers()
    reports, amendments = file_index()
    return get_filings(headers, reports, amendments)

if __name__ == "__main__":
    import tools
    tools.export(parse_committees())
    tools.export(parse_transfers())
    tools.export(parse_contributions())
    tools.export(parse_candidates())
    tools.export(parse_transfers())
    #tools.export(parse_efilings())

#result = read_fec_file("WEBL08.DAT",WEB_ROW_DEF,WEB_ROW_DEF_SIZE)
#result = read_fec_file("cansum04.txt",CANSUM_ROW_DEF,CANSUM_ROW_DEF_SIZE)
#result = read_fec_file("CANSUM94.DAT",CANSUM_94_ROW_DEF,CANSUM_94_ROW_DEF_SIZE)
#result = read_fec_file("CANSUM90.DAT",CANSUM_90_ROW_DEF,CANSUM_90_ROW_DEF_SIZE)
#result = read_fec_file("cansum88.dat",CANSUM_88_ROW_DEF,CANSUM_88_ROW_DEF_SIZE)
#print result
