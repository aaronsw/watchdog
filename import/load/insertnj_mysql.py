#!/usr/bin/python
import web, insertnj
db = web.database(dbn='mysql', db='watchdog_dev')
if __name__ == '__main__':
    insertnj.db = db
    insertnj.main()
