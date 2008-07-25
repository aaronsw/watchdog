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
  
  gini float,
  -- @@other IRS stuff
);

CREATE TABLE zip2dist (
  zip int references zip,
  district varchar(10) references district,
  
  primary key (zip, district)
);

CREATE TABLE politician (
  -- index.json
  id varchar(256) primary key,
  district varchar(10) references district,
  wikipedia varchar(256),
  
  -- govtrack.json
  bioguideid varchar(256),
  opensecretsid varchar(256),
  govtrackid varchar(256),
  gender varchar(1),
  birthday varchar(256),        -- we don't really want DateTime objects
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
  photo_credit_text varchar(256)
  
  -- fec
  money_raised int,
  pct_spent float,
  pct_self float,
  pct_indiv float,
  pct_pac float
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

-- Views
CREATE VIEW v_politician_name  AS (SELECT id, firstname, lastname, id || ' ' || firstname || ' ' || lastname AS name FROM politician);

-- Permissions
GRANT ALL on state TO watchdog;
GRANT ALL on district TO watchdog;
GRANT ALL on politician TO watchdog;
GRANT ALL on interest_group_rating TO watchdog;
GRANT ALL on interest_group TO watchdog;
GRANT ALL on bill TO watchdog;
GRANT ALL on vote TO watchdog;
GRANT ALL on interest_group_bill_support TO watchdog;
GRANT ALL on group_politician_similarity TO watchdog;
GRANT ALL on category TO watchdog;
GRANT ALL on v_politician_name to watchdog;
GRANT ALL on politician_fec_ids to watchdog;
