CREATE TABLE site (id int PRIMARY KEY NOT NULL, name text, wunder_key text, operator text, email text, phone text, location text, longitude text, latitude text, twilio_acct_sid text, twilio_auth_token text);
CREATE TABLE assets (id int PRIMARY KEY NOT NULL, name text, unit text, virtual int, context text, system text, enabled int, data_field text);
CREATE TABLE schedule(id int PRIMARY KEY NOT NULL, job_name TEXT, asset_id int, command TEXT, time_unit TEXT, interval INT, at_time TEXT, enabled INT, sequence text, virtual int);
CREATE TABLE sequence (id int PRIMARY KEY NOT NULL, name TEXT, command TEXT, step INT, step_name TEXT, timeout INT);
CREATE TABLE alert_params (asset_id int, lower_threshold real, upper_threshold real, message text, response_type text);
CREATE TABLE db_info (schema_version text, data_version text);
