CREATE TABLE rtus (rtuid text, protocol text, address text, version text, online int);
CREATE TABLE pins (rtuid text, pin text, mode int, def_value int, pos int);
CREATE TABLE interval_schedule(job_id int PRIMARY KEY NOT NULL, job_name TEXT, command TEXT, time_unit TEXT, interval INT, at_time TEXT, enabled INT);
