DROP TABLE IF EXISTS state CASCADE;
DROP TABLE IF EXISTS district CASCADE;
DROP TABLE IF EXISTS politician CASCADE;
DROP TABLE IF EXISTS interest_group_ratings CASCADE;
DROP TABLE IF EXISTS interest_group_rating CASCADE;
DROP TABLE IF EXISTS interest_group CASCADE;
DROP TABLE IF EXISTS bill CASCADE;
DROP TABLE IF EXISTS vote CASCADE;
DROP TABLE IF EXISTS interest_group_bill_support CASCADE;
DROP TABLE IF EXISTS group_politician_similarity CASCADE;
DROP TABLE IF EXISTS category CASCADE;
DROP TABLE IF EXISTS contribution CASCADE;
DROP TABLE IF EXISTS expenditure CASCADE;
DROP TABLE IF EXISTS wyr CASCADE;
DROP VIEW IF EXISTS census CASCADE;
DROP TABLE IF EXISTS census_data CASCADE;
DROP TABLE IF EXISTS census_meta CASCADE;
DROP TABLE IF EXISTS soi CASCADE;

CREATE TABLE state (
  -- index.json
  code varchar(2) primary key,
  name varchar(256),
  status varchar(256),
  wikipedia varchar(256),
  fipscode varchar(2)
);

CREATE TABLE district (
  -- index.json
  name varchar(10) primary key,
  district int,
  state varchar(2) references state,
  voting boolean,
  wikipedia varchar(256),
  
  -- almanac.json
  almanac varchar(256),
  area_sqmi int,
  cook_index varchar(10),
  poverty_pct real,
  median_income int,
  est_population int,           -- most recent population estimate
  est_population_year int,      -- year of the estimate
  
  -- shapes.json
  outline text, -- geojson
  
  -- centers.json
  center_lat real,
  center_lng real,
  zoom_level int
);

CREATE TABLE zip (
  zip varchar(5) primary key,
  city text,
  state varchar(2), --references states, (@@no AE=Armed Forces Europe)
  gini real
  -- @@other IRS stuff
);

CREATE TABLE zip4 (
  zip varchar(5), --references zip, (seems some ZIP+4s aren't in ctyst?)
  plus4 varchar(4),
  district varchar(10) --references district,
  --primary key (zip, plus4)  
);

----alter table zip4 drop constraint zip4_pkey;
--COPY zip4 FROM  '/home/watchdog/web/data/load/zip4.tsv';
--alter table zip4 add primary key (zip, plus4);
--alter table zip4 add constraint "zip4_district_fkey" FOREIGN KEY (district) REFERENCES district(name) #@@
--GRANT ALL ON zip4 TO watchdog;

CREATE TABLE census_meta (
  internal_key varchar(10),
  census_type smallint,
  hr_key varchar(512)
);
ALTER TABLE census_meta ADD primary key (internal_key, census_type);
CREATE TABLE census_data (
  distric_id varchar(10),
  internal_key varchar(10),
  census_type smallint,   -- 1 or 3
  value numeric
);
ALTER TABLE census_data ADD primary key (district_id, internal_key, census_type);
CREATE VIEW census AS select * from census_meta NATURAL JOIN census_data;

CREATE TABLE soi (
  district_id varchar(10),
  -- irs/soi
  bracket_low int,

  agi numeric,
  n_dependents numeric,
  n_eitc numeric,
  n_filers numeric,
  n_prepared numeric,

  tot_charity numeric,
  tot_eitc numeric,
  tot_tax numeric,

  avg_dependents numeric,
  avg_eitc numeric,
  avg_income numeric,
  avg_taxburden numeric,

  pct_charity numeric,
  pct_eitc numeric,
  pct_prepared numeric
);
alter table soi add primary key (district_id, bracket_low);

CREATE TABLE politician (
  -- index.json
  id varchar(256) primary key,
  district varchar(10) references district,
  wikipedia varchar(256),
  
  -- govtrack.json --@@get from votesmart?
  bioguideid varchar(256),
  opensecretsid varchar(256),
  govtrackid varchar(256),
  gender varchar(1),
  birthday varchar(256),        -- we don't really want DateTime objects --why not? --ASw
  firstname varchar(256),
  middlename varchar(256),
  lastname varchar(256),
  officeurl varchar(256),
  party varchar(256),
  religion varchar(256),
  n_bills_introduced int,
  n_bills_enacted int,
  n_bills_debated int,
  n_bills_cosponsored int,
  n_speeches int,
  words_per_speech int,
  
  -- voteview.json
  icpsrid int,
  nominate real,
  predictability real,
  
  -- earmarks.json
  amt_earmark_requested int default 0,
  n_earmark_requested int default 0,
  n_earmark_received int default 0,
  amt_earmark_received int default 0,
  
  -- photos.json
  photo_path varchar(256),
  photo_credit_url varchar(256),
  photo_credit_text varchar(256),
  
  -- fec
  money_raised int,
  pct_spent float,
  pct_self float,
  pct_indiv float,
  pct_pac float,
  
  -- votesmart
  nickname varchar(256),
  votesmartid varchar(256),
  birthplace varchar(256),
  education text,
  
  -- punch
  chips2008 float,
  progressive2008 float,
  progressiveall float,
  
  -- opensecrets
  pct_pac_business float
);

CREATE TABLE politician_fec_ids (
  politician_id varchar(256) references politician,
  fec_id varchar(256),
  -- cycle int,
  primary key (politician_id, fec_id)
);

CREATE TABLE interest_group (
  id serial primary key,
  groupname varchar(10), 
  category_id varchar(10), -- references category,
  longname varchar(256) UNIQUE
);

CREATE TABLE interest_group_rating (  -- interest group scores for politicians
  id serial primary key, -- does web.py require this? otherwise let's drop it
  politician_id varchar(256) references politician,
  -- almanac.json
  year int,                     -- 2005, 2006, etc.
  group_id int references interest_group,
  rating int                    -- typically 0-100
);

CREATE TABLE bill (
  id varchar(256) primary key,
  session int,
  type varchar(5),
  number int,
  introduced date,
  title text,
  sponsor varchar(256) references politician,
  summary text,
  maplightid varchar(10),
  
  -- computed from vote
  yeas int,
  neas int
);

CREATE TABLE vote (
  bill_id varchar(256) references bill,
  politician_id varchar(256) references politician,
  vote int2,
  primary key (bill_id, politician_id)
);

CREATE TABLE interest_group_bill_support(
  bill_id varchar(256) references bill,
  group_id int references interest_group,
  support int2,
  primary key (bill_id, group_id)
);

CREATE TABLE group_politician_similarity(
  group_id int references interest_group,
  politician_id varchar(256) references politician,
  agreed int,
  total int,
  primary key (politician_id, group_id)  
);

CREATE TABLE category(
  id varchar(10) primary key,
  name varchar(256),
  industry varchar(256),
  sector varchar(256) 
);

CREATE TABLE contribution(
  id serial primary key,
  politician_id varchar(256) references politician,
  committee varchar(256),
  contrib_date date, 
  contributor_org varchar(256), 
  contributor varchar(256), 
  occupation varchar(256), 
  employer varchar(256), 
  candidate_name varchar(256),
  filer_id varchar(10), 
  report_id int, 
  amount varchar(20)
);

CREATE TABLE expenditure(
  id serial primary key,
  committee varchar(256),
  expenditure_date date, 
  recipient varchar(256), 
  filer_id varchar(10), 
  report_id int, 
  candidate_name varchar(256),
  amount varchar(20)
);

CREATE TABLE wyr(
    district varchar(6) references district,
    contact varchar(255),
    contacttype varchar(1),    -- E=email, W=wyr, I=ima, Z=zipauth
    captcha boolean
);
    

-- Views
CREATE VIEW v_politician_name  AS (SELECT id, firstname, lastname, id || ' ' || firstname || ' ' || lastname AS name FROM politician);

-- Permissions
GRANT ALL on state TO watchdog;
GRANT ALL on district TO watchdog;
GRANT ALL ON zip TO watchdog;
GRANT ALL ON zip4 TO watchdog;
GRANT ALL on politician TO watchdog;
GRANT ALL on interest_group_rating TO watchdog;
GRANT ALL on interest_group TO watchdog;
GRANT ALL on bill TO watchdog;
GRANT ALL on vote TO watchdog;
GRANT ALL on interest_group_bill_support TO watchdog;
GRANT ALL on group_politician_similarity TO watchdog;
GRANT ALL on category TO watchdog;
GRANT ALL on wyr TO watchdog;
GRANT ALL on v_politician_name to watchdog;
GRANT ALL on politician_fec_ids to watchdog;
GRANT ALL on contribution to watchdog;
GRANT ALL on expenditure to watchdog;
