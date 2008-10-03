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

LOADERS = .schema .json \
          .almanac .centers .voteview .govtrack \
          .bills .interests .votesmart .photos .fec .census .soi .earmarks

all: database
clean:
	rm $(LOADERS)

cleanload:
	rm $(TSVS)

cleanparse:
	rm $(NJS)

database: $(LOADERS)

.manual: .schema load/manual.py load/manual/*.json
	python load/manual.py
	touch $@

.schema: ../schema.py
	python -c "import schema; schema.sql.recreate(); schema.sql.grantall('watchdog')"
	touch $@

# not currently using .shapes
.shapes: .json load/shapes.py parse/shapes.py
	$(PYTHON) load/shapes.py
	touch $@

.almanac: .json load/almanac.py parse/almanac.py
	$(PYTHON) load/almanac.py
	touch $@

.centers: .json load/govtrack_gis.py ../data/crawl/govtrack/gis/gmapdata/*
	$(PYTHON) load/govtrack_gis.py
	touch $@

$(LOAD)/politicians/index.json: load/manual/politicians.json
	mkdir -p $(LOAD)/politicians
	cp $< $@

.govtrack: load/govtrack.py parse/govtrack.py ../data/crawl/govtrack/us/110/repstats/*xml .json
	$(PYTHON) load/govtrack.py
	touch $@

.voteview: .json load/voteview.py parse/voteview.py ../data/crawl/voteview/
	$(PYTHON) load/voteview.py
	touch $@

.earmarks: load/earmarks.py .govtrack .voteview
	$(PYTHON) load/earmarks.py
	touch $@

.bills: .govtrack load/bills.py
	$(PYTHON) load/bills.py

.interests: load/maplight.py .bills
	$(PYTHON) load/maplight.py
	touch $@

.votesmart: .json .govtrack load/votesmart.py $(CRAWL)/votesmart/bios.json $(CRAWL)/votesmart/candidates.json
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

.soi: .schema .json
	$(PYTHON) load/soi.py
	touch $@

$(LOAD)/census_meta.tsv $(LOAD)/census_data.tsv: load/census.py parse/census.py
	python load/census.py

.census: $(LOAD)/census_meta.tsv $(LOAD)/census_data.tsv .schema .json
	$(DBCLIENT) $(WATCHDOG_TABLE) < $(LOAD)/census_meta.tsv 
	$(DBCLIENT) $(WATCHDOG_TABLE) < $(LOAD)/census_data.tsv 
	touch $@

# new way of doing things: parse to .njs files

USPS_FILES = $(PARSE)/usps/ctystate.njs.gz \
             $(PARSE)/usps/5digit.njs.gz \
             $(PARSE)/usps/tiger.njs.gz \
             $(PARSE)/usps/tigerdat.njs.gz \
             $(PARSE)/usps/zip4.njs.gz \
             $(PARSE)/usps/zip4dist.njs.gz \
             $(PARSE)/usps/all5digitzip.txt \

parse: $(NJS) parse_usps

parse_usps: $(USPS_FILES)
	echo "Haven't scripted generation of these yet."

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
