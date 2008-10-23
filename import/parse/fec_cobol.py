"""
Parser for FEC Files for files that conform to webl.txt and weball.txt
"""

__author__ = [
  "Jeremy Schwartz <jerschwartz@gmail.com>",
  "Aaron Swartz <me@aaronsw.com>",
]

import re, os, sys, gzip, glob
import web
from fixed_width import get_len, enum, filler, parse_file

COBOL_INT_TABLE = dict(']0 j1 k2 l3 m4 n5 o6 p7 q8 r9'.split())
def integer(d):
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

def string(d):
    return d.decode('cp1251').rstrip()

def date(d):
    """where `d` is like MMDDYYYY"""
    return d[4:8] + "-" + d[0:2] + "-" + d[2:4]

def date2(d):
    "??DDMMYYYY"
    return d[6:10] + "-" + d[4:6] + "-" + d[2:4]

party = enum(**{"1": "Democratic", "2": "Republican", "3": "Other"})

ico = enum(**{" ": " ", "I": "Incumbent", "C": "Challenger", "O": "Open Seat"})

filing_freq = enum(M="Monthly", Q="Quarterly", T="Terminated")

cmte_type = enum(
    C="COMMUNICATION COST",
    D="DELEGATE",
    H="HOUSE",
    I="INDEPENDENT EXPENDITURE (PERSON OR GROUP, NOT A COMMITTEE)",
    N="NON-PARTY NON-QUALIFIED",
    P="PRESIDENTIAL",
    Q="QUALIFIED NON-PARTY (SEE 2 USC 441(A)(4))",
    S="SENATE",
    X="NON-QUALIFIED PARTY",
    Y="QUALIFIED PARTY (SEE 2 USC 441(A)(4))",
    Z="NATIONAL PARTY ORGANIZATION. NON FED ACCT."
)

cmte_desig = enum(
    A="AUTHORIZED BY A CANDIDATE",
    J="JOINT FUND RAISER",
    P="PRINCIPAL CAMPAIGN COMMITTEE OF A CANDIDATE",
    U="UNAUTHORIZED"
)

def_webl = [
  ('_type', 0, lambda x: 'Candidate'),
  ("candidate_id", 9, string),
  ("candidate_name", 38, string),
  ("ico", 1, ico),
  ("party", 1, party),
  ("party_desig", 3, string),
  ("total_receipts", 10, integer),
  ("auth_trans_from", 10, integer),
  ("total_disbursements", 10, integer),
  ("trans_to_auth", 10, integer),
  ("begin_cash", 10, integer),
  ("end_cash", 10, integer),
  ("contrib_from_candidate", 10, integer),
  ("loans_from_candidate", 10, integer),
  ("other_loans", 10, integer),
  ("candidate_loan_repay", 10, integer),
  ("other_loan_repay", 10, integer),
  ("debts_owed_by", 10, integer),
  ("total_indiv_contrib", 10, integer),
  ("state_code", 2, string),
  ("district", 2, string),
  ("spec_elec_status", 1, enum),
  ("primary_elec_status", 1, enum),
  ("runoff_elec_status", 1, enum),
  ("general_elec_status", 1, enum),
  ("general_elec_pct", 3, string),
  ("contrib_from_other_pc", 10, integer),
  ("contrib_from_pc", 10, integer),
  ("end_date", 8, date),
  ("refunds_to_indiv", 10, integer),
  ("refunds_to_commit", 10, integer),
  (None, 2, filler)
]

# Supports files for CANSUM04 CANSUM02 CANSUM00 CANSUM98 CANSUM96
def_cansum = [
  ('_type', 0, lambda x: 'Cadidate'),
  ("candidate_id", 9, string),
  ("candidate_name", 38, string),
  ("ico", 1, ico),
  ("party", 1, party),
  ("party_desig", 3, string),
  ("total_receipts", 10, integer),
  ("auth_trans_from", 10, integer),
  ("total_disbursments", 10, integer),
  ("trans_from_auth", 10, integer),
  ("begin_cash", 10, integer),
  ("end_cash", 10, integer),
  ("contrib_from_candidate", 10, integer),
  ("loans_from_candidate", 10, integer),
  ("other_loans", 10, integer),
  ("candidate_loan_repay", 10, integer),
  ("other_loan_repay", 10, integer),
  ("debts_owed_by", 10, integer),
  ("contrib_200_499", 10, integer),
  ("total_200_499", 10, integer),
  ("contrib_500_749", 10, integer),
  ("total_500_749", 10, integer),
  ("contrib_750", 10, integer),
  ("total_750", 10, integer),
  ("total_indiv_contrib", 10, integer),
  ("major_pty_contrib", 10, integer),
  ("party_indep_expend_for", 10, integer),
  ("corp_contrib", 10, integer),
  ("labor_contrib", 10, integer),
  ("non_connected_contrib", 10, integer),
  ("tmh_contrib", 10, integer),
  ("coop_contrib", 10, integer),
  ("corp_wo_stock_contrib", 10, integer),
  ("non_party_exp", 10, integer),
  ("non_party_exp_agn", 10, integer),
  ("indep_exp_for", 10, integer),
  ("indep_exp_agn", 10, integer),
  ("comm_cost_for", 10, integer),
  ("comm_cost_agn", 10, integer),
  ("state_code", 2, string),
  ("district", 2, string),
  ("spec_elec_status", 1, string),
  ("primary_elec_status", 1, string),
  ("runoff_elec_status", 1, string),
  ("gen_elec_status", 1, string),
  ("gen_elec_pct", 7, integer),
  ("spec_elec_cand", 1, string),
  ("party_coord_exp", 10, integer),
  ("party_indep_exp", 10, integer),
  (None, 2, filler)
]

# Supports format CANSUM94 CANSUM92
def_cansum92 = [
  ('_type', 0, lambda x: 'Candidate'),
  ("candidate_id", 9, string),
  ("candidate_name", 38, string),
  ("ico", 1, ico),
  ("party", 1, party),
  ("party_desig", 3, string),
  ("total_reciepts", 10, integer),
  ("auth_trans_from", 10, integer),
  ("total_disbursments", 10, integer),
  ("trans_to_auth", 10, integer),
  ("begin_cash", 10, integer),
  ("end_cash", 10, integer),
  ("contrib_from_cand", 10, integer),
  ("loans_from_cand", 10, integer),
  ("other_loans", 10, integer),
  ("cand_loans_repay", 10, integer),
  ("other_loan_repay", 10, integer),
  ("debts_owned_by", 10, integer),
  ("contrib_200_499", 10, integer),
  ("total_200_499", 10, integer),
  ("contrib_500_749", 10, integer),
  ("total_500_749", 10, integer),
  ("contrib_750", 10, integer),
  ("total_750", 10, integer),
  ("total_indiv_contrib", 10, integer),
  ("major_pty_contrib", 10, integer),
  ("pty_coord_expend", 10, integer),
  ("corp_contrib", 10, integer),
  ("labor_contrib", 10, integer),
  ("non_connect_cont", 10, integer),
  ("tmh_contrib", 10, integer),
  ("coop_contrib", 10, integer),
  ("corp_wo_stock", 10, integer),
  ("non_party_exp", 10, integer),
  ("non_party_exp_agn", 10, integer),
  ("indep_exp_for", 10, integer),
  ("indep_exp_agn", 10, integer),
  ("comm_cost_for", 10, integer),
  ("comm_cost_agn", 10, integer),
  ("state_code", 2, string),
  ("district", 2, string),
  ("spec_elec_status", 1, string),
  ("primary_elec_status", 1, string),
  ("runoff_elec_status", 1, string),
  ("gen_elec_status", 7, string),
  ("spec_elec_cand", 1, string),
  (None, 2, filler)
]

def_cansum90 = [
  ('_type', 0, lambda x: 'Candidate'),
  ("candidate_id", 9, string),
  ("candidate_name", 38, string),
  ("ico", 1, ico),
  ("fill", 10, string),
  ("party", 1, party),
  ("party_desig", 3, string),
  ("total_reciepts", 12, integer),
  ("auth_trans_from", 12, integer),
  ("total_disbursments", 12, integer),
  ("trans_to_auth", 12, integer), #9
  ("begin_cash", 12, integer),
  ("end_cash", 12, integer),
  ("contrib_from_cand", 12, integer),
  ("loans_from_cand", 12, integer),
  ("other_loans", 12, integer),
  ("cand_loans_repay", 12, integer),
  ("other_loan_repay", 12, integer),
  ("debts_owned_by", 12, integer),
  ("contrib_200_499", 8, integer),
  ("total_200_499", 12, integer), #19
  ("contrib_500_749", 8, integer),
  ("total_500_749", 12, integer),
  ("contrib_750", 8, integer),
  ("total_750", 12, integer),
  ("total_indiv_contrib", 12, integer),
  ("major_pty_contrib", 12, integer),
  ("pty_coord_expend", 12, integer),
  ("corp_contrib", 12, integer),
  ("labor_contrib", 12, integer),
  ("non_connect_cont", 12, integer), #29
  ("tmh_contrib", 12, integer), #30
  ("coop_contrib", 12, integer),
  ("corp_wo_stock", 12, integer),
  ("non_party_exp", 12, integer),
  ("non_party_exp_agn", 12, integer),
  ("indep_exp_for", 12, integer),
  ("indep_exp_agn", 12, integer),
  ("comm_cost_for", 12, integer),
  ("comm_cost_agn", 12, integer), #38
  ("state_code", 2, string),
  ("district", 2, string),
  ("spec_elec_status", 1, string),
  ("primary_elec_status", 1, string),
  ("runoff_elec_status", 1, string),
  ("gen_elec_status", 1, string),
  ("spec_elec_cand", 1, string),
  (None, 2, filler)
]

def_cansum88 = [
  ('_type', 0, lambda x: 'Candidate'),
  ("candidate_id", 9, string),
  ("candidate_name", 38, string),
  ("ico", 1, ico),
  ("fill", 10, string),
  ("party", 1, party),
  ("party_desig", 3, string),
  ("total_reciepts", 12, integer),
  ("auth_trans_from", 12, integer),
  ("total_disbursments", 12, integer),
  ("trans_to_auth", 12, integer), #9
  ("begin_cash", 12, integer),
  ("end_cash", 12, integer),
  ("contrib_from_cand", 12, integer),
  ("loans_from_cand", 12, integer),
  ("other_loans", 12, integer),
  ("cand_loans_repay", 12, integer),
  ("other_loan_repay", 12, integer),
  ("debts_owned_by", 12, integer),
  ("contrib_500_749", 8, integer),
  ("total_500_749", 12, integer),
  ("contrib_750", 8, integer),#20
  ("total_750", 12, integer),
  ("total_indiv_contrib", 12, integer),
  ("major_pty_contrib", 12, integer),
  ("pty_coord_expend", 12, integer),
  ("corp_contrib", 12, integer),
  ("labor_contrib", 12, integer),
  ("non_connect_cont", 12, integer),
  ("tmh_contrib", 12, integer),
  ("coop_contrib", 12, integer),
  ("corp_wo_stock", 12, integer),#30
  ("non_party_exp", 12, integer),
  ("non_party_exp_agn", 12, integer),
  ("indep_exp_for", 12, integer),
  ("indep_exp_agn", 12, integer),
  ("comm_cost_for", 12, integer),
  ("comm_cost_agn", 12, integer),
  ("state_code", 2, string),
  ("district", 2, string),
  ("spec_elec_status", 1, string),
  ("primary_elec_status", 1, string),
  ("runoff_elec_status", 1, string),
  ("gen_elec_status", 1, string),
  ("spec_elec_cand", 1, string),
  (None, 2, filler)
]

def_pas2 = [
  ('_type', 0, lambda x: 'Transfer'),
  ("from_committee_id", 9, string),
  ("amendment_status", 1, enum),
  ("report_type", 3, enum),
  ("primary_general", 1, enum),
  ("microfilm_loc", 11, string),
  ("type", 3, enum), #@@@@ important enumeration
  ("date", 8, date),
  ("amount", 7, integer),
  ("to_other_id", 9, string),
  ("to_candidate_id", 9, string),
  ("fec_record_id", 7, string),
  (None, 2, filler)
]

def_cm = [
  ('_type', 0, lambda x: 'Committee'),
  ("committee_id", 9, string),
  ("committee_name", 90, string),
  ("treasurer_name", 38, string),
  ("street_one", 34, string),
  ("street_two", 34, string),
  ("city", 18, string),
  ("state", 2, string),
  ("zip", 5, string),
  ("committee_designation", 1, enum),
  ("committee_type", 1, enum),
  ("committee_party", 3, enum),
  ("filing_frequency", 1, enum),
  ("interest_group_category", 1, enum(
    C='CORPORATION',
    L='LABOR ORGANIZATION',
    M='MEMBERSHIP ORGANIZATION',
    T='TRADE ASSOCIATION',
    V='COOPERATIVE',
    W='CORPORATION WITHOUT CAPITAL STOCK')),
  ("connected_org_name", 38, string),
  ("candidate_id", 9, string),
  (None, 2, filler)
]

def_webk = [
  ('_type', 0, lambda x: 'PAC/PARTY'),
  ("id", 9, string),
  ("name", 90, string),
  ("type", 1, cmte_type),
  ("desig", 1, cmte_desig),
  ("filing_freq", 1, filing_freq),
  ("total_receipts", 10, integer),
  ("trans_from_aff", 10, string),
  ("contrib_rec_from_indiv", 10, integer),
  ("contrib_rec_from_other_pc", 10, integer),
  ("contrib_from_cand", 10, integer),
  ("cand_loans", 10, integer),
  ("total_loans_rec", 10, integer),
  ("total_disbursment", 10, integer),
  ("trans_to_aff", 10, integer),
  ("refunds_to_indiv", 10, integer),
  ("refunds_to_other_pc", 10, integer),
  ("cand_loan_repayments", 10, integer),
  ("loan_repayments", 10, integer),
  ("cash_begin", 10, integer),
  ("cash_close", 10, integer),
  ("debts_bowned_by", 10, integer),
  ("nonfederal_trans_rec", 10, integer),
  ("contrib_made_to_other", 10, integer),
  ("indep_exped_made", 10, string),
  ("party_coord_expend_made", 10, integer),
  ("nonfederal_share_of_expend", 10, integer),
  ("month", 2, integer),
  ("day", 2, integer),
  ("year", 4, integer),
  (None, 2, filler)
]

#Supporst PACSUM[92-04]
def_pacsum = [
  ('_type', 0, lambda x: 'PAC'),
  ("committee_id", 9, string),
  ("committee_name", 90, string),
  ("sig", 1, string),
  ("end_coverage_date", 6, date),
  ("total_receipts", 10, integer),
  ("trans_from_aff", 10, integer),
  ("contrib_from_party", 10, integer),
  ("contrib_from_non_party", 10, integer),
  ("total_indiv_contrib", 10, integer),
  ("indiv_contrib_200+", 10, integer),
  ("in_kind_contrib", 10, integer),
  ("total_disbursements", 10, integer),
  ("trans_to_aff", 10, integer),
  ("contrib_to_party", 10, integer),
  ("contrib_to_non_party", 10, integer),
  ("indiv_contrib_refund", 10, integer),
  ("begin_cash", 10, integer),
  ("end_cash", 10, integer),
  ("debts_owed_to", 10, integer),
  ("debts_owed_by", 10, integer),
  ("total_in_kind_contrib", 10, integer),
  ("total_1999_contrib", 10, integer),
  ("total_for", 10, integer),
  ("total_against", 10, integer),
  ("pres_contrib_dem", 10, integer),
  ("pres_contrib_rep", 10, integer),
  ("pres_contrib_oth", 10, integer),
  ("senate_contrib_dem", 10, integer),
  ("senate_contrib_rep", 10, integer),
  ("senate_contrib_oth", 10, integer),
  ("house_contrib_dem", 10, integer),
  ("house_contrib_rep", 10, integer),
  ("house_contrib_oth", 10, integer),
  ("senate_inc_contrib", 10, integer),
  ("senate_cha_contrib", 10, integer),
  ("senate_opn_contrib", 10, integer),
  ("house_inc_contrib", 10, integer),
  ("house_cha_contrib", 10, integer),
  ("house_opn_contrib", 10, integer),
  ("non_federal_trans", 10, integer),
  ("non_federal_expend", 10, integer),
  (None, 2, filler)
]

# Supports PACSUM[84-90]
def_pacsum90 = [
  ('_type', 0, lambda x: 'PAC'),
  ("committee_id", 9, string),
  ("committee_name", 90, string),
  ("sig", 1, string),
  ("end_coverage_date", 10, date2),
  ("total_receipts", 12, integer),
  ("contrib_from_aff", 12, integer),
  ("contrib_from_party", 12, integer),
  ("contrib_from_non_party", 12, integer),
  ("indiv_contrib", 12, integer),
  ("total_contrib", 12, integer),
  ("in_kind_contrib", 12, integer),
  ("total_disbursements", 12, integer),
  ("contrib_to_non_party_aff", 12, integer),
  ("contrib_to_party", 12, integer),
  ("contrib_to_non_party", 12, integer),
  ("indiv_contrib_refund", 12, integer),
  ("begin_cash_year_1", 12, integer),
  ("end_cash_year_2", 12, integer),
  ("debts_owed_to", 12, integer),
  ("debts_owed_by", 12, integer),
  ("total_in_kind_contrib", 12, integer),
  ("total_1_contrib", 12, integer),
  ("total_indep_for", 12, integer),
  ("total_indep_against", 12, integer),
  ("pres_contrib_dem", 12, integer),
  ("pres_contrib_rep", 12, integer),
  ("pres_contrib_oth", 12, integer),
  ("senate_contrib_dem", 12, integer),
  ("senate_contrib_rep", 12, integer),
  ("senate_contrib_oth", 12, integer),
  ("house_contrib_dem", 12, integer),
  ("house_contrib_rep", 12, integer),
  ("house_contrib_oth", 12, integer),
  ("senate_inc_contrib", 12, integer),
  ("senate_cha_contrib", 12, integer),
  ("senate_opn_contrib", 12, integer),
  ("house_inc_contrib", 12, integer),
  ("house_cha_contrib", 12, integer),
  ("house_opn_contrib", 12, integer),
  (None, 2, filler)
]


# Supports PACSUM[80-82]
def_pacsum82 = [
  ('_type', 0, lambda x: 'PAC'),
  ("committee_id", 9, string),
  ("committee_name", 90, string),
  ("committee_type", 1, string),
  ("sig", 1, string),
  ("party", 3, string),
  ("not_used", 1, string),
  ("state", 2, string),
  ("total_receipts", 10, integer),
  ("trans_in_party", 10, integer),
  ("trans_in_party_other", 10, integer),
  ("corp_contrib", 10, integer),
  ("labor_contrib", 10, integer),
  ("non_connected_contrib", 10, integer),
  ("tmh_contrib", 10, integer),
  ("coop_contrib", 10, integer),
  ("corp_wo_stock_contrib", 10, integer),
  ("num_cand_contrib_to", 10, integer),
  ("total_party_contrib", 10, integer),
  ("not_used2", 10, string),
  ("not_used3", 10, string),
  ("contrib_500+", 10, integer),
  ("total_disbursements", 10, integer),
  ("trans_out_party_same", 10, integer),
  ("trans_out_party_other", 10, integer),
  ("total_contrib", 10, integer),
  ("not_used4", 80, string),
  ("latest_cash_on_hand", 10, integer),
  ("jan_1_cash_on_hand", 10, integer),
  ("debts_owed_to", 10, integer),
  ("debts_owed_by", 10, integer),
  ("in_kind_contrib", 10, integer),
  ("contrib_refunds", 10, integer),
  ("contrib_to_dem_pres", 10, integer),
  ("contrib_to_rep_pres", 10, integer),
  ("contrib_to_other_pres", 10, integer),
  ("contrib_to_dem_senate", 10, integer),
  ("contrib_to_rep_senate", 10, integer),
  ("contrib_to_other_senate", 10, integer),
  ("contrib_to_dem_house", 10, integer),
  ("contrib_to_rep_house", 10, integer),
  ("contrib_to_other_house", 10, integer),
  ("expend_on_dem_pres", 10, integer),
  ("expend_on_rep_pres", 10, integer),
  ("expend_on_other_pres", 10, integer),
  ("expend_on_dem_senate", 10, integer),
  ("expend_on_rep_senate", 10, integer),
  ("expend_on_other_senate", 10, integer),
  ("expend_on_dem_house", 10, integer),
  ("expend_on_rep_house", 10, integer),
  ("expend_on_other_house", 10, integer),
  ("end_coverage_date", 8, date),
  ("senate_house_inc_contrib", 9, integer),
  ("senate_house_cha_contrib", 9, integer),
  ("senate_house_opn_contrib", 9, integer),
  (None, 2, filler)
]

def_indiv = [
  ('_type', 0, lambda x: 'Individual Contribution'),
  ('filer_id', 9, string),
  ('amendment_type', 1, enum),
  ('report_type', 3, enum),
  ('primary_general', 1, enum),
  ('microfilm_loc', 11, string),
  ('transaction_type', 3, enum), #@@important enumeration
  ('src_name', 34, string),
  ('src_city', 18, string),
  ('src_state', 2, string),
  ('src_zip', 5, string),
  ('src_occupation', 35, string),
  ('date', 8, date),
  ('amount', 7, integer),
  ('src_id', 9, string),
  ('fec_record_id', 7, string),
  (None, 2, filler)
]

def_cn = [
  ('_type', 0, lambda x: 'Candidate'),
  ('candidate_id', 9, string),
  ('candidate_name', 38, string),
  ('party_desig_1', 3, string),
  ('party_desig_2', 3, string),
  ('party_desig_3', 3, string),
  ('ico', 1, ico),
  (None, 1, filler),
  ('candidate_status', 1, enum(
    C="STATUTORY CANDIDATE",
    F="STATUTORY CANDIDATE FOR A FUTURE ELECTION",
    N="NOT YET A STATUTORY CANDIDATE",
    P="STATUTORY CANDIDATE IN PRIOR CYCLE")),
  ('street_one', 34, string),
  ('street_two', 34, string),
  ('city', 18, string),
  ('state', 2, string),
  ('zip', 5, string),
  ('principal_cmte_id', 9, string),
  ('election_year', 2, string),
  ('current_district', 2, string),
  (None, 2, filler)
]

def parse_cansum():
    return parse_file(def_webl, file("../data/crawl/fec/2008/weball.dat"))
def parse_candidates():
    for fn in glob.glob('../data/crawl/fec/*/cn.dat'):
        for elt in parse_file(def_cn, file(fn)):
            yield elt
def parse_committees():
    for fn in glob.glob('../data/crawl/fec/*/cm.dat'):
        for elt in parse_file(def_cm, file(fn)):
            yield elt
def parse_transfers():
    for fn in glob.glob('../data/crawl/fec/*/pas2.dat'):
        for elt in parse_file(def_pas2, file(fn)):
            yield elt
def parse_contributions():
    for fn in glob.glob('../data/crawl/fec/*/indiv.dat.gz'):
        for elt in parse_file(def_indiv, gzip.open(fn)):
            yield elt

if __name__ == "__main__":
    import tools
    tools.export(parse_candidates())
    tools.export(parse_committees())
    tools.export(parse_transfers())
    tools.export(parse_contributions())
