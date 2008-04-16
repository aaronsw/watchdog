COMMAND_LINE_OPTIONS = 

all: test
	./webapp.py $(COMMAND_LINE_OPTIONS)

test:
	./webapp_test.py
