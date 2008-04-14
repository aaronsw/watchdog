PARSE=../data/parse
DBCLIENT=psql

all: .database

.database: ../schema.sql load/json.py $(PARSE)/states/index.json $(PARSE)/districts/index.json $(PARSE)/districts/almanac.json $(PARSE)/districts/shapes.json $(PARSE)/politicians/index.json $(PARSE)/politicians/govtrack.json $(PARSE)/politicians/photos.json
	$(DBCLIENT) watchdog_dev < ../schema.sql
	python load/json.py
	touch .database


$(PARSE)/states/index.json: parse/manual/states.json
	cp parse/manual/states.json $(PARSE)/states/index.json

$(PARSE)/districts/index.json: parse/manual/districts.json
	cp parse/manual/districts.json $(PARSE)/districts/index.json

$(PARSE)/districts/almanac.json: load/almanac.py parse/almanac.py
	PYTHONPATH=. python load/almanac.py > $(PARSE)/districts/almanac.json.tmp
	mv $(PARSE)/districts/almanac.json.tmp $(PARSE)/districts/almanac.json

$(PARSE)/districts/shapes.json: load/shapes.py
	PYTHONPATH=. python load/shapes.py > $(PARSE)/districts/shapes.json

$(PARSE)/politicians/index.json: parse/manual/politicians.json
	cp parse/manual/politicians.json $(PARSE)/politicians/index.json

$(PARSE)/politicians/govtrack.json: load/govtrack.py parse/govtrack.py
	PYTHONPATH=. python load/govtrack.py > $(PARSE)/politicians/govtrack.json.tmp
	mv $(PARSE)/politicians/govtrack.json.tmp $(PARSE)/politicians/govtrack.json

$(PARSE)/politicians/photos.json: load/photos.py $(PARSE)/politicians/govtrack.json
	PYTHONPATH=. python load/photos.py > $(PARSE)/politicians/photos.json.tmp
	mv $(PARSE)/politicians/photos.json.tmp $(PARSE)/politicians/photos.json


