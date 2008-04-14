PARSE=../data/parse
DBCLIENT=psql
PYTHON=PYTHONPATH=.:$(PYTHONPATH) python
JSONS=$(PARSE)/states/index.json \
      $(PARSE)/districts/index.json \
      $(PARSE)/districts/almanac.json \
      $(PARSE)/districts/shapes.json \
      $(PARSE)/politicians/index.json \
      $(PARSE)/politicians/govtrack.json \
      $(PARSE)/politicians/photos.json \
      $(PARSE)/districts/centers.json

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

$(PARSE)/states/index.json: parse/manual/states.json
	cp parse/manual/states.json $(PARSE)/states/index.json

$(PARSE)/districts/index.json: parse/manual/districts.json
	cp parse/manual/districts.json $(PARSE)/districts/index.json

$(PARSE)/districts/almanac.json: load/almanac.py parse/almanac.py
	$(PYTHON) load/almanac.py > $(PARSE)/districts/almanac.json.tmp
	mv $(PARSE)/districts/almanac.json.tmp $(PARSE)/districts/almanac.json

$(PARSE)/districts/shapes.json: load/shapes.py
	$(PYTHON) load/shapes.py > $(PARSE)/districts/shapes.json

$(PARSE)/districts/centers.json: load/govtrack_gis.py
	$(PYTHON) load/govtrack_gis.py > $(PARSE)/districts/centers.json

$(PARSE)/politicians/index.json: parse/manual/politicians.json
	cp parse/manual/politicians.json $(PARSE)/politicians/index.json

$(PARSE)/politicians/govtrack.json: load/govtrack.py parse/govtrack.py
	$(PYTHON) load/govtrack.py > $(PARSE)/politicians/govtrack.json.tmp
	mv $(PARSE)/politicians/govtrack.json.tmp $(PARSE)/politicians/govtrack.json

$(PARSE)/politicians/photos.json: load/photos.py $(PARSE)/politicians/govtrack.json
	$(PYTHON) load/photos.py > $(PARSE)/politicians/photos.json.tmp
	mv $(PARSE)/politicians/photos.json.tmp $(PARSE)/politicians/photos.json


