DROP TABLE state CASCADE;
DROP TABLE district CASCADE;
DROP TABLE politician CASCADE;

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
  birthday date,
  firstname varchar(256),
  middlename varchar(256),
  lastname varchar(256),
  officeurl varchar(256),
  party varchar(256),
  religion varchar(256),
  
  -- photos.json
  photo_path varchar(256),
  photo_credit_url varchar(256),
  photo_credit_text varchar(256)
);

GRANT ALL on state TO watchdog;
GRANT ALL on district TO watchdog;
GRANT ALL on politician TO watchdog;

