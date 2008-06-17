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
	rm $(JSONS) .schema .json .bills interest .database

.database: .schema .json .bills .interests
	touch $@

.json: .schema load/json.py $(JSONS)
	python load/json.py
	touch $@

.schema: ../schema.sql
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

$(LOAD)/politicians/govtrack.json: load/govtrack.py parse/govtrack.py ../data/crawl/govtrack/us/110/repstats/
	$(PYTHON) load/govtrack.py > $@.tmp
	mv $@.tmp $@

$(LOAD)/politicians/photos.json: load/photos.py $(LOAD)/politicians/govtrack.json
	$(PYTHON) load/photos.py > $@.tmp
	mv $@.tmp $@

$(LOAD)/politicians/earmarks.json: load/earmarks.py $(LOAD)/politicians/govtrack.json
	$(PYTHON) load/earmarks.py > $@.tmp
	mv $@.tmp $@

.bills: .schema load/bills.py .json
	$(PYTHON) load/bills.py
	touch $@

.interests: .schema load/maplight.py .bills
	$(PYTHON) load/maplight.py
	touch $@
