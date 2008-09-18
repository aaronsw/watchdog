import commands
import simplejson
import os
import urllib

DEBUG = True
out_dir = '../../../data/crawl/mortality/%s.tsv'
states = simplejson.load(file('../../../data/load/states/index.json'))
URL = 'http://wonder.cdc.gov/controller/datarequest/D35'
# POST data for ordering by 1) Region and 2) Cause of Death, Some State, Saving as File, and (max) 10 minute timeout
data = 'javascript=on&stage=request&M_1=D35.M1&M_2=D35.M2&M_3=D35.M3&O_vintage=D35&B_1=D35.V9-level2&B_2=D35.V2-level3&B_3=*None*&B_4=*None*&B_5=*None*&O_title=&O_location=D35.V9&finder-stage-D35.V9=codeset&O_V9_fmode=freg&V_D35.V9=&F_D35.V9=%s&I_D35.V9=%s&finder-stage-D35.V10=codeset&O_V10_fmode=freg&V_D35.V10=&F_D35.V10=*All*&I_D35.V10=&O_age=D35.V5&V_D35.V5=*All*&V_D35.V6=00&V_D35.V1=*All*&V_D35.V8=*All*&V_D35.V7=*All*&V_D35.V11=*All*&O_icd=D35.V2&finder-stage-D35.V2=codeset&O_V2_fmode=freg&V_D35.V2=&F_D35.V2=*All*&I_D35.V2=&finder-stage-D35.V4=codeset&O_V4_fmode=freg&V_D35.V4=&F_D35.V4=*All*&I_D35.V4=&V_D35.V12=*All*&V_D35.V13=*All*&O_rate_per=100000&O_aar=aar_none&O_aar_pop=0000&VM_D35.M6_D35.V1=*All*&VM_D35.M6_D35.V7=*All*&VM_D35.M6_D35.V8=*All*&VM_D35.M6_D35.V10=&O_change_action=Export+Results&O_show_totals=true&O_precision=1&O_timeout=600&action=Send'

# iterate across states in /data/parse/states/index.json
for abbr,s in states.iteritems():
    if abbr == 'PW' or s['status'] != 'state' or os.path.exists(out_dir % abbr):
        continue
    fipscode = s['fipscode']
    name = s['name']
    state_plus_fipscode = '%s+%%28%s%%29%%0D%%0A' % (fipscode, urllib.quote(name))
    cmd = 'curl -s -o %s %s -d \'%s\'' % (out_dir % abbr, URL, data % (fipscode, state_plus_fipscode))
    if DEBUG:
        print 'logging: %s' % cmd
    status = os.system(cmd)
    if status != 0:
        print 'program aborted. failed at %s' % cmd
        exit
