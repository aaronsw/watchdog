"""
Load Project Vote Smart data.
"""

import json
import tools
from settings import db

cans = json.load(file('../data/crawl/votesmart/candidates.json'))
bios = json.load(file('../data/crawl/votesmart/bios.json'))

def main():
    for dist, canl in cans.iteritems():
        dist=dist.replace("-SEN1","").replace("-SEN2","") ## JT: Hack
        for can in canl:
            wid = tools.getWatchdogID(dist,can['lastName'])
            if wid:
                bio = bios[can['candidateId']]['candidate']
                db.update('politician', where='id = $wid', vars=locals(),
                  votesmartid=can['candidateId'], 
                  nickname=can['nickName'],
                  birthplace=bio['birthPlace'],
                  education=bio['education'].replace('\r\n', '\n')
                )
              
if __name__ == "__main__": main()
