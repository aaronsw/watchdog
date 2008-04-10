#!/usr/bin/python
"A tiny little bit of glue to run the web app with MySQL."
import webapp, web
if __name__ == '__main__':
    webapp.db = web.database(dbn='mysql', db='watchdog_dev')
    webapp.app.run()
