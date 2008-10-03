"""
load data from govtrack.us
"""

import web
from parse import govtrack
import tools
from settings import db

mapping = {
  'bioguideid': 'bioguideid',
  'birthday': 'birthday',
  'firstname': 'firstname',
  'gender': 'gender',
  'id': 'govtrackid',
  'lastname': 'lastname',
  'middlename': 'middlename',
  'osid': 'opensecretsid',
  'party': 'party',
  'religion': 'religion',
  'represents': 'district_id',
  'url': 'officeurl'
}

def combine():
    watchdog_map = {}
    govtrack_map = {}

    for pol in govtrack.parse_basics():
        watchdog_id = tools.getWatchdogID(pol.get('represents'),pol.lastname)
        if watchdog_id:
            govtrack_map[pol.id] = watchdog_map[watchdog_id] = newpol = web.storage()
        else:
            continue

        for k, v in mapping.iteritems():
            if k in pol: newpol[v] = pol[k]
    
    for pol in govtrack.parse_stats([
      'enacted', 'introduced', 'cosponsor', 'speeches']):
        if pol.id not in govtrack_map:
            continue
        else:
            newpol = govtrack_map[pol.id]
    
        if pol.get('SponsorEnacted'):
            newpol.n_bills_introduced = int(pol.NumSponsor)
            newpol.n_bills_enacted = int(pol.SponsorEnacted)
    
        if pol.get('SponsorIntroduced'):
            newpol.n_bills_debated = int(pol.NumSponsor) - int(pol.SponsorIntroduced)
    
        if pol.get('NumCosponsor'):
            newpol.n_bills_cosponsored = int(pol.NumCosponsor)
    
        if pol.get('Speeches'):
            newpol.n_speeches = int(pol.Speeches)
            newpol.words_per_speech = int(pol.WordsPerSpeech)
    
    return watchdog_map

def main():
    for k, v in combine().iteritems():
        db.update('politician', where='id=$k', vars=locals(), **v)

if __name__ == "__main__": main()
