COMMAND_LINE_OPTIONS = 
export PYTHONPATH:= ./vendor/

all: test
	./webapp.py $(COMMAND_LINE_OPTIONS)

test:
	./webapp_test.py
