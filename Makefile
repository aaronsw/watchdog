COMMAND_LINE_OPTIONS = 
export PYTHONPATH := $(PWD)/vendor/:$(PYTHONPATH)

all: sync test run

run:
	./webapp.py $(COMMAND_LINE_OPTIONS)

test:
	cd import/parse; ./almanac_test.py
	utils/rdftramp.py
	import/parse/tools.py
	import/load/tools.py
	./webapp_test.py

sync: rsync gitsync

rsync:
	rsync -avzu watchdog.net:~watchdog/web/data .

gitsync:
	git pull
