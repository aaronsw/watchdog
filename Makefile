COMMAND_LINE_OPTIONS = 
export PYTHONPATH := $(PWD)/vendor/:$(PYTHONPATH)

all: test run

run:
	./webapp.py $(COMMAND_LINE_OPTIONS)

test:
	cd import/parse; ./almanac_test.py
	utils/rdftramp.py
	./webapp_test.py
