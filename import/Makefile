SQL=psql
INSERT=./insertnj.py
all:
	cat ../schema.sql | $(SQL) watchdog_dev
	$(INSERT)
