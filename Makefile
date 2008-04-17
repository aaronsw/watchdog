COMMAND_LINE_OPTIONS = 
export PYTHONPATH:= $(PWD)/vendor/:$(PYTHONPATH)

all: test
	./webapp.py $(COMMAND_LINE_OPTIONS)

test:
	cd import/parse; ./almanac_test.py
	./webapp_test.py
