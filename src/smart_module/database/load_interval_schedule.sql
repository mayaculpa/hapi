-- HAPI Data Table Creation Script v1.0
-- Author: Tyler Reed
-- Release: June 24th, 2016
--*********************************************************************
--Copyright 2016 Maya Culpa, LLC
--
--This program is free software: you can redistribute it and/or modify
--it under the terms of the GNU General Public License as published by
--the Free Software Foundation, either version 3 of the License, or
--(at your option) any later version.
--
--This program is distributed in the hope that it will be useful,
--but WITHOUT ANY WARRANTY; without even the implied warranty of
--MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--GNU General Public License for more details.
--
--You should have received a copy of the GNU General Public License
--along with this program.  If not, see <http://www.gnu.org/licenses/>.
--*********************************************************************
INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (1, "VRS Lights On", "RTU1", "doc0220", 'day', -1, "00:00", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (2, "VRS Lights Off", "RTU1", "doc0221", 'day', -1, "15:55", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (3, "VRS Feed Pump Off", "RTU1", "doc0231", 'day', 14, "08:30", 0);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (4, "VRS Flush Pump On", "RTU1", "doc0240", 'day', 14, "08:30", 0);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (5, "VRS Flush Pump Off", "RTU1", "doc0241", 'day', 14, "08:32", 0);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (6, "VRS Feed Pump On", "RTU1", "doc0230", 'day', 14, "08:32", 0);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (7, "Log Data", "RTU1", "env", 'minute', 10, "", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (8, "Log Status", "RTU1", "sta", 'minute', 60, "", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (9, "Log Weather", "virtual", "get_weather()", 'minute', 10, "", 1);
