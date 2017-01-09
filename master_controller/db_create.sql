CREATE TABLE rtus (rtuid text, name text, protocol text, address text, version text, online int);
CREATE TABLE pins (rtuid text, name text, pin text, mode int, def_value int, pos int);
CREATE TABLE assets (asset_id int, rtuid text, abbreviation text, name text, pin text, unit text, context text, system text);
CREATE TABLE interval_schedule(job_id int PRIMARY KEY NOT NULL, job_name TEXT, command TEXT, time_unit TEXT, interval INT, at_time TEXT, enabled INT, rtuid text, sequence text, timeout float);
CREATE TABLE log (rtuid text, timestamp text, data text);
CREATE TABLE sensor_data (asset_id int, timestamp text, unit text, value float);
CREATE TABLE command_log (rtuid text, timestamp text, command text);
CREATE TABLE site (site_id int, name text, wunder_key text, operator text, email text, phone text, location text, longitude text, latitude text, net_iface text, serial_port text);
CREATE TABLE sequence (sequence_id int PRIMARY KEY NOT NULL, name TEXT, command TEXT, step INT, step_name TEXT, timeout INT);
CREATE TABLE alert_params (asset_id int, lower_threshold real, upper_threshold real, message text, response_type text);
CREATE TABLE alert_log (asset_id int, value real, timestamp text);

