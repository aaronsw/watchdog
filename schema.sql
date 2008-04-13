DROP TABLE state, district, politician CASCADE;

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
  njfilename varchar(256), -- temporary, I assume
  area_sqmi int,
  cook_index varchar(10),
  poverty_pct real,
  median_income int,
  est_population_2005 int,
  
  -- shapes.json
  outline text -- geojson
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
  religion varchar(256)
);
