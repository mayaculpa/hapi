# HAPI Data Table Creation Script v1.0
# Author: Tyler Reed
# Release: June 24th, 2016
#*********************************************************************
#Copyright 2016 Maya Culpa, LLC
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
#*********************************************************************

CREATE TABLE rtus (rtuid text, name text, protocol text, address text, version text, online int);
CREATE TABLE pins (rtuid text, name text, pin text, mode int, def_value int, pos int);
CREATE TABLE assets (asset_id int, rtuid text, abbreviation text, name text, pin text, unit text);
CREATE TABLE interval_schedule(job_id int PRIMARY KEY NOT NULL, job_name TEXT, command TEXT, time_unit TEXT, interval INT, at_time TEXT, enabled INT, rtuid text);
CREATE TABLE log (rtuid text, timestamp text, data text);
CREATE TABLE sensor_data (asset_id int, timestamp text, unit text, value float);
CREATE TABLE command_log (rtuid text, timestamp text, command text);
CREATE TABLE site (site_id int, name text, wunder_key text, operator text, email text, phone text, location text, longitude text, latitude text);


