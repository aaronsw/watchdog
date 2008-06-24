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

-- save contacts imported from yahoo, google etc.,
-- emails can be 64+1+255 char 
CREATE TABLE contacts(
    uemail VARCHAR(320);
    cemail VARCHAR(320);
    cname VARCHAR(80);
    provider VARCHAR(20);
);

GRANT ALL ON users TO watchdog;
GRANT ALL ON petition TO watchdog;
GRANT ALL ON signatory TO watchdog;
GRANT ALL ON contacts TO watchdog;