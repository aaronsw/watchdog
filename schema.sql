DROP TABLE district;

CREATE TABLE district (
  -- index.json
  name varchar(10) primary key,
  district int,
  state varchar(2),
  voting boolean,
  wikipedia varchar(256),
  
  -- almanac.json
  njfilename varchar(256), -- temporary, I assume
  area_sqmi int,
  cook_index varchar(10),
  poverty_pct real,
  median_income int
);
