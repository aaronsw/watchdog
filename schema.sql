DROP TABLE district;

CREATE TABLE district (
  name varchar(10) primary key,
  state varchar(2),
  district int,
  cook_index varchar(10),
  area_sqmi int,
  poverty_pct real,
  median_income int
);