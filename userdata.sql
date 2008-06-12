-- All the tables for user data 

CREATE TABLE users(
    id serial primary key,
    name varchar(256),
    password varchar(256),
    email varchar(320) UNIQUE -- max allowed email length.
);

CREATE TABLE petition(
    id varchar(256) primary key,
    title text,
    description text,
    owner_id int references users,
    created timestamp default now()  
);

CREATE TABLE signatory(
    user_id int references users,
    petition_id varchar(256) references petition,
    UNIQUE (user_id, petition_id)
);

GRANT ALL on users TO watchdog;
GRANT ALL on petition TO watchdog;
GRANT ALL on signatory TO watchdog;
