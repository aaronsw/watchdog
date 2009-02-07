import os, sys
import json
import tools
from parse import govtrack, votesmart

ALL_PEOPLE_FILE = "../data/load/politicians/all_people.json"
MANUAL_JSON = "./load/manual/all_people.json"

def load_wd_mapping():
    print "Loading ID mapping."
    if os.path.isfile(MANUAL_JSON):
        return json.load(file(MANUAL_JSON)) # Load previous version of this generation
    return {}
def reverse_map(map, old_key, new_key):
    new_map = {}
    for id, x in map.items():
        x[old_key] = id
        if new_key in x:
            new_map[x[new_key]] = x
    return new_map

def load_gt_to_wd():
    wd_mapping = load_wd_mapping()
    return reverse_map(wd_mapping, 'watchdog_id', 'govtrack_id')

def load_vs_to_wd():
    wd_mapping = load_wd_mapping()
    return reverse_map(wd_mapping, 'watchdog_id', 'votesmart_id')

def blarb(f):
    to_wd = f()
    def get_wd_id(gt_id):
        return to_wd.get(gt_id)
    return get_wd_id
get_wd_id_GT = blarb(load_gt_to_wd)
get_wd_id_VS = blarb(load_vs_to_wd)


def gen_pol_id(pol):
    firstname = pol.get('firstName') or pol.get('firstname')
    lastname = pol.get('lastName') or pol.get('lastname')
    suffix = pol.get('suffix') or pol.get('namemod') or ''
    if suffix: suffix = '_'+suffix
    id = tools.id_ify(firstname.lower()+'_'+lastname.lower()+suffix.lower())
    return id

def generate_ids():
    wd_to_gt = load_wd_mapping()
    # Govtrack
    for pol in govtrack.parse_basics():
        current_member = False
        collision = False
        watchdog_id = tools.getWatchdogID(pol.get('represents'),pol.lastname)
        if watchdog_id:
            current_member = True
            # pol.represents should always be the same as current_member, if we
            # remove the origional politician.json file we can use that
            # instead.
            assert(pol.represents)
        else:
            assert(not pol.get('represents'))
            watchdog_id = gen_pol_id(pol)
            if watchdog_id in wd_to_gt and \
                    wd_to_gt[watchdog_id]['govtrack_id'] != pol.id: 
                collision = True
        if (not collision) or current_member:
            if watchdog_id not in wd_to_gt: 
                wd_to_gt[watchdog_id] = {}
            wd_to_gt[watchdog_id]['govtrack_id'] = pol.id
        if collision: 
            wd_to_gt[watchdog_id]['collision'] = True
        if current_member: 
            wd_to_gt[watchdog_id]['current_member'] = True
    # Votesmart
    for district, cands in votesmart.candidates():
        district=tools.fix_district_name(district)
        for pol in cands:
            watchdog_id = tools.getWatchdogID(district, pol['lastName'])
            if not watchdog_id:
                watchdog_id = gen_pol_id(pol)
            vsid=pol['candidateId']
            #TODO: Could use some more checking to be sure we are 1. adding the
            #      correct votesmart id to the correct watchdog_id (eg. in the
            #      case that there was a collision in processing the govtrack
            #      data). And 2. aren't creating a new watchdog_id when there
            #      was already one for this person.
            if watchdog_id not in wd_to_gt:
                wd_to_gt[watchdog_id] = {}
            wd_to_gt[watchdog_id]['votesmart_id'] = vsid
    return wd_to_gt


if __name__ == "__main__": 
    if not os.path.isfile(ALL_PEOPLE_FILE):
        print "Generating govtrack to watchdog id mapping."
        fd = open(ALL_PEOPLE_FILE,'w')
        fd.write(json.dumps(generate_ids(), indent=2, sort_keys=True))
        fd.write('\n')
        fd.close()
