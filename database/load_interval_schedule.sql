INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (1, "VRS Lights On", "RTU1", "doc0220", 'day', -1, "00:00", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (2, "VRS Lights Off", "RTU1", "doc0221", 'day', -1, "15:55", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (3, "VRS Feed Pump Off", "RTU1", "doc0231", 'day', 14, "08:30", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (4, "VRS Flush Pump On", "RTU1", "doc0240", 'day', 14, "08:30", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (5, "VRS Flush Pump Off", "RTU1", "doc0241", 'day', 14, "08:32", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (6, "VRS Feed Pump On", "RTU1", "doc0230", 'day', 14, "08:32", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (7, "Log Data", "RTU1", "env", 'minute', 1, "", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (8, "Log Status", "RTU1", "sta", 'minute', 60, "", 1);

INSERT INTO interval_schedule(job_id, job_name, rtuid, command, time_unit, interval, at_time, enabled)
VALUES (9, "Log Weather", "virtual", "get_weather()", 'minute', 5, "", 1);