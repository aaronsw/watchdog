CREATE TABLE person(
       id INTEGER 
       	  UNIQUE NOT NULL, 
       lastname VARCHAR(80),
       firstname VARCHAR(80),
       middlename VARCHAR(80),
       namemod VARCHAR(10),
       religion VARCHAR(80),
       nickname VARCHAR(40),
       birthday DATE NULL,
       gender VARCHAR(1),
       url TEXT,
       party VARCHAR(80),
       osid VARCHAR(10),
       bioguideid VARCHAR(10),
       title VARCHAR(80),
       state VARCHAR(2),
       district VARCHAR(2),
       name VARCHAR(100)
);


CREATE SEQUENCE prole_serial START 1;
CREATE TABLE prole(
       id INTEGER 
       	  DEFAULT nextval('prole_serial')
       	  UNIQUE NOT NULL,
       person_id INTEGER REFERENCES person(id),
       "type" VARCHAR(80),
       startdate DATE,
       enddate DATE,
       party VARCHAR(100),
       state VARCHAR(2),
       district VARCHAR(2),
       url TEXT
);


CREATE SEQUENCE committee_serial START 1;
CREATE TABLE COMMITTEE(
       id INTEGER 
       	  DEFAULT nextval('committee_serial') 
       	  UNIQUE NOT NULL,
       committee TEXT,
       subcommittee TEXT NULL
);


CREATE SEQUENCE committee_assignment_serial START 1;
CREATE TABLE committee_assignment(
       id INTEGER 
       	  DEFAULT nextval('committee_assignment_serial') 
       	  UNIQUE NOT NULL,
       prole_id INTEGER REFERENCES prole(id),
       committee_id INTEGER REFERENCES committee(id),
       "role" VARCHAR(255)
);

-- delete 

DROP TABLE committee_assignment;
DROP SEQUENCE committee_assignment_serial;
DROP TABLE committee;
DROP SEQUENCE committee_serial;
DROP TABLE prole;
DROP SEQUENCE prole_serial;
DROP TABLE person;
