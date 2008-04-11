PARSE=../data/parse
DBCLIENT=psql

all: .database

.database: ../schema.sql $(PARSE)/states/index.json $(PARSE)/districts/index.json $(PARSE)/districts/almanac.json $(PARSE)/districts/shapes.json
	$(DBCLIENT) watchdog_dev < ../schema.sql
	python load/insertjson.py
	touch .database

$(PARSE)/states/index.json: parse/manual/states.json
	cp parse/manual/states.json $(PARSE)/states/index.json

$(PARSE)/districts/index.json: parse/manual/districts.json
	cp parse/manual/districts.json $(PARSE)/districts/index.json

$(PARSE)/districts/almanac.json: load/loadalmanac.py parse/scrapenj.py
	PYTHONPATH=. python load/loadalamanac.py > $(PARSE)/districts/almanac.json

$(PARSE)/districts/shapes.json: load/loaddistshapes.py
	PYTHONPATH=. python load/loaddistshapes.py > $(PARSE)/districts/shapes.json
