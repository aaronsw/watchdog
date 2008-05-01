ifeq ($(DATABASE_ENGINE),mysql)
    DBCLIENT=mysql
else ifeq ($(DATABASE_ENGINE),sqlite)
    DBCLIENT=sqlite3
else
    DBCLIENT=psql
endif

export PYTHONPATH := .:$(PWD)/../vendor:$(PYTHONPATH)

PYTHON=python

LOAD=../data/load
JSONS=$(LOAD)/states/index.json \
      $(LOAD)/districts/index.json \
      $(LOAD)/interest_groups.json \
      $(LOAD)/districts/almanac.json \
      $(LOAD)/districts/shapes.json \
      $(LOAD)/politicians/index.json \
      $(LOAD)/politicians/govtrack.json \
      $(LOAD)/politicians/photos.json \
      $(LOAD)/politicians/earmarks.json \
      $(LOAD)/districts/centers.json

all: .database
clean:
	rm $(JSONS) .schema

.database: .schema load/json.py $(JSONS)
	python load/json.py
	touch $@

# .schema is separated into a separate target so you can "touch
# .schema" when you get some crap like this:
# ERROR 1142 (42000) at line 64: GRANT command denied to user ''@'localhost' for table 'state'
# Depends on $(JSONS) so you don't end up dropping all the
# database tables when you have an error generating the .json files.
.schema: ../schema.sql $(JSONS)
	$(DBCLIENT) watchdog_dev < $<
	touch $@

$(LOAD)/states/index.json: load/manual/states.json
	mkdir -p $(LOAD)/states
	cp $< $@

$(LOAD)/districts/index.json: load/manual/districts.json
	mkdir -p $(LOAD)/districts
	cp $< $@

# from nationaljournal
$(LOAD)/interest_groups.json: load/manual/interest_groups.json
	mkdir -p $(LOAD)
	cp $< $@

$(LOAD)/districts/almanac.json: load/almanac.py parse/almanac.py
	$(PYTHON) load/almanac.py > $@.tmp
	mv $@.tmp $@

$(LOAD)/districts/shapes.json: load/shapes.py
	$(PYTHON) load/shapes.py > $@

$(LOAD)/districts/centers.json: load/govtrack_gis.py
	$(PYTHON) load/govtrack_gis.py > $@

$(LOAD)/politicians/index.json: load/manual/politicians.json
	mkdir -p $(LOAD)/politicians
	cp $< $@

$(LOAD)/politicians/govtrack.json: load/govtrack.py parse/govtrack.py
	$(PYTHON) load/govtrack.py > $@.tmp
	mv $@.tmp $@

$(LOAD)/politicians/photos.json: load/photos.py $(LOAD)/politicians/govtrack.json
	$(PYTHON) load/photos.py > $@.tmp
	mv $@.tmp $@

$(LOAD)/politicians/earmarks.json: load/earmarks.py $(LOAD)/politicians/govtrack.json
	$(PYTHON) load/earmarks.py > $@.tmp
	mv $@.tmp $@

