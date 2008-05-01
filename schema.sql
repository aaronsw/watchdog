DROP TABLE IF EXISTS state CASCADE;
DROP TABLE IF EXISTS district CASCADE;
DROP TABLE IF EXISTS politician CASCADE;
DROP TABLE IF EXISTS interest_group_ratings CASCADE;
DROP TABLE IF EXISTS interest_group_rating CASCADE;
DROP TABLE IF EXISTS interest_group CASCADE;

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
  n_speeches int,
  words_per_speech int,

  -- earmarks.json
  amt_earmark_requested int,
  n_earmark_requested int,
  n_earmark_received int,
  amt_earmark_received int,
  
  -- photos.json
  photo_path varchar(256),
  photo_credit_url varchar(256),
  photo_credit_text varchar(256)
);

CREATE TABLE interest_group (
  groupname varchar(10) primary key,
  longname varchar(256)
);

CREATE TABLE interest_group_rating (  -- interest group scores for politicians
  id serial primary key, -- does web.py require this? otherwise let's drop it
  politician_id varchar(256) references politician,
  -- almanac.json
  year int,                     -- 2005, 2006, etc.
  groupname varchar(10) references interest_group,
  rating int                    -- typically 0-100
);

GRANT ALL on state TO watchdog;
GRANT ALL on district TO watchdog;
GRANT ALL on politician TO watchdog;
GRANT ALL on interest_group_rating TO watchdog;
GRANT ALL on interest_group TO watchdog;
