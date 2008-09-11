ifeq ($(DATABASE_ENGINE),mysql)
    DBCLIENT=mysql
else ifeq ($(DATABASE_ENGINE),sqlite)
    DBCLIENT=sqlite3
else
    DBCLIENT=psql
endif

ifeq ($(WATCHDOG_TABLE),)
    WATCHDOG_TABLE=watchdog_dev
endif

export PYTHONPATH := ../:.:$(PWD)/../vendor:$(PYTHONPATH)

PYTHON=python

CRAWL=../data/crawl
PARSE=../data/parse
LOAD=../data/load
JSONS=$(LOAD)/states/index.json \
      $(LOAD)/districts/index.json \
      $(LOAD)/interest_groups.json \
      $(LOAD)/districts/almanac.json \
      $(LOAD)/districts/shapes.json \
      $(LOAD)/politicians/index.json \
      $(LOAD)/politicians/govtrack.json \
      $(LOAD)/politicians/voteview.json \
      $(LOAD)/politicians/earmarks.json \
      $(LOAD)/districts/centers.json

TSVS=$(LOAD)/bill.tsv \
	 $(LOAD)/vote.tsv \
	 $(LOAD)/zip4.tsv \
	 $(LOAD)/census_meta.tsv \
	 $(LOAD)/census_data.tsv

NJS=$(PARSE)/almanac.njs \
    $(PARSE)/earmarks.njs \
    $(PARSE)/fec.njs \
    $(PARSE)/govtrack.njs \
    $(PARSE)/soi.njs \
    $(PARSE)/voteview.njs

all: database
clean:
	-rm $(JSONS) .schema .json .bills .interests .votesmart .photos .fec .census .soi

cleanparse:
	rm $(NJS)

database: .schema .json .bills .interests .votesmart .photos .fec .census .soi

.json: .schema load/json.py $(JSONS)
	python load/json.py
	touch $@

.schema: ../schema.py
	python -c "import schema; schema.sql.recreate()"
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

$(LOAD)/politicians/govtrack.json: load/govtrack.py parse/govtrack.py ../data/crawl/govtrack/us/110/repstats/*xml
	$(PYTHON) load/govtrack.py > $@.tmp
	mv $@.tmp $@

$(LOAD)/politicians/voteview.json: load/voteview.py parse/voteview.py ../data/crawl/voteview/
	$(PYTHON) load/voteview.py > $@.tmp
	mv $@.tmp $@

$(LOAD)/politicians/earmarks.json: load/earmarks.py $(LOAD)/politicians/govtrack.json
	$(PYTHON) load/earmarks.py > $@.tmp
	mv $@.tmp $@

$(LOAD)/bill.tsv $(LOAD)/vote.tsv: load/bills.py
	$(PYTHON) load/bills.py

.bills: $(LOAD)/bill.tsv $(LOAD)/vote.tsv .schema
	$(DBCLIENT) $(WATCHDOG_TABLE) < $(LOAD)/bill.tsv
	$(DBCLIENT) $(WATCHDOG_TABLE) < $(LOAD)/vote.tsv
	touch $@

.interests: load/maplight.py .bills
	$(PYTHON) load/maplight.py
	touch $@

.votesmart: .json load/votesmart.py $(CRAWL)/votesmart/bios.json $(CRAWL)/votesmart/candidates.json
	$(PYTHON) load/votesmart.py
	touch $@

.photos: .json .votesmart load/photos.py
	$(PYTHON) load/photos.py
	touch $@

.fec: .json
	$(PYTHON) load/fec.py
	touch $@

.zip4: $(LOAD)/zip4.tsv .json
	# NOTE: leaving the index on while loading the data is unbearably slow. If
	#       the schema changes this makefile will need to be updated too.
	#       Also, our districts table is missing MH-00 (Marshall Islands) and
	#       thus the foreign key must be removed.
	echo "ALTER TABLE zip4 DROP CONSTRAINT zip4_pkey; \
ALTER TABLE zip4 DROP CONSTRAINT zip4_district_id_fkey; \
COPY zip4 (zip,plus4,district_id) FROM '${PWD}/../data/load/zip4.tsv'; \
ALTER TABLE zip4 ADD FOREIGN KEY (district_id) REFERENCES district; \
ALTER TABLE zip4 ADD PRIMARY KEY (zip,plus4); \
		" | $(DBCLIENT) $(WATCHDOG_TABLE)
	touch $@

.soi: .schema .json .zip4
	$(PYTHON) load/soi.py
	touch $@

$(LOAD)/census_meta.tsv $(LOAD)/census_data.tsv: load/census.py parse/census.py
	python load/census.py

.census: $(LOAD)/census_meta.tsv $(LOAD)/census_data.tsv .schema .json
	$(DBCLIENT) $(WATCHDOG_TABLE) < $(LOAD)/census_meta.tsv 
	$(DBCLIENT) $(WATCHDOG_TABLE) < $(LOAD)/census_data.tsv 
	touch $@

# new way of doing things: parse to .njs files

parse: $(NJS)

$(PARSE)/almanac.njs: parse/almanac.py 
	$(PYTHON) parse/almanac.py --dump > $@.tmp
	mv $@.tmp $@

$(PARSE)/earmarks.njs: parse/earmarks.py $(CRAWL)/taxpayer/bigkahuna.xls
	$(PYTHON) parse/earmarks.py > $@.tmp
	mv $@.tmp $@

$(PARSE)/fec.njs: parse/fec.py $(CRAWL)/fec
	$(PYTHON) parse/fec.py > $@.tmp
	mv $@.tmp $@

$(PARSE)/govtrack.njs: parse/govtrack.py
	$(PYTHON) parse/govtrack.py > $@.tmp
	mv $@.tmp $@

$(PARSE)/soi.njs: parse/soi.py $(CRAWL)/irs/soi/
	$(PYTHON) parse/soi.py > $@.tmp
	mv $@.tmp $@

$(PARSE)/voteview.njs: parse/voteview.py
	$(PYTHON) parse/voteview.py > $@.tmp
	mv $@.tmp $@
