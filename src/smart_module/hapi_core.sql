-- #1 (First) database schema.
-- CREATE TABLE site (id int PRIMARY KEY NOT NULL, name text, wunder_key text, operator text, email text, phone text, location text, longitude text, latitude text, twilio_acct_sid text, twilio_auth_token text);
-- CREATE TABLE assets (id int PRIMARY KEY NOT NULL, name text, unit text, virtual int, context text, system text, enabled int, data_field text);
-- CREATE TABLE schedule(id int PRIMARY KEY NOT NULL, name TEXT, asset_id int, command TEXT, time_unit TEXT, interval INT, at_time TEXT, enabled INT, sequence text, virtual int);
-- CREATE TABLE sequence (id int PRIMARY KEY NOT NULL, name TEXT, command TEXT, step INT, step_name TEXT, timeout INT);
-- CREATE TABLE alert_params (asset_id int, lower_threshold real, upper_threshold real, message text, response_type text);
-- CREATE TABLE db_info (schema_version text, data_version text);

-- #2 (Second) database schema.
CREATE TABLE site (id INT PRIMARY KEY NOT NULL, name TEXT NOT NULL, wunder_key TEXT, operator TEXT, email TEXT, phone TEXT, location TEXT, longitude TEXT, latitude TEXT);
CREATE TABLE sequence (id INT PRIMARY KEY NOT NULL, name TEXT, command TEXT, step INT, step_name TEXT, timeout INT);
CREATE TABLE db_info (schema_version TEXT, data_version TEXT);
CREATE TABLE schedule(id INT PRIMARY KEY NOT NULL, name TEXT, asset_id INT, command TEXT, time_unit TEXT, interval INT, at_time TEXT, enabled INT, sequence TEXT, virtual INT);
CREATE TABLE assets (id TEXT PRIMARY KEY NOT NULL, name TEXT, unit TEXT, virtual INT, context TEXT, system TEXT, enabled INT);
CREATE TABLE alert_params(asset_id TEXT PRIMARY KEY NOT NULL, lower_threshold REAL NOT NULL, upper_threshold REAL NOT NULL, message TEXT, response_type TEXT NOT NULL, notify_enabled INT NOT NULL);
CREATE TABLE mail_settings(id INT PRIMARY KEY NOT NULL, serveraddr TEXT NOT NULL, serverport TEXT NOT NULL, username TEXT NOT NULL, password TEXT NOT NULL, sender TEXT, receiver TEXT NOT NULL, tls INT NOT NULL);
CREATE TABLE influx_settings(id INT PRIMARY KEY NOT NULL, server TEXT NOT NULL, port INT NOT NULL, username TEXT NOT NULL, password TEXT NOT NULL);
CREATE TABLE twilio_settings(id INT PRIMARY KEY NOT NULL, sender text NOT NULL, receiver TEXT NOT NULL, twilio_acct_sid TEXT NOT NULL, twilio_auth_token TEXT NOT NULL);
