"""
Load Project Vote Smart data.
"""

import simplejson
import tools
from settings import db

cans = simplejson.load(file('../data/crawl/votesmart/candidates.json'))
bios = simplejson.load(file('../data/crawl/votesmart/bios.json'))

def main():
    for dist, canl in cans.iteritems():
        for can in canl:
            wid = tools.districtp(dist)
            if wid and can['lastName'].lower() in wid:
                bio = bios[can['candidateId']]['candidate']
                db.update('politician', where='id = $wid', vars=locals(),
                  votesmartid=can['candidateId'], 
                  nickname=can['nickName'],
                  birthplace=bio['birthPlace'],
                  education=bio['education'].replace('\r\n', '\n')
                )
              
if __name__ == "__main__": main()
