DROP TABLE district;
DROP TABLE state;

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
