INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (1, "RTU1", "ResTemp", "Reservoir Temperature", "res1tmp", "Celsius");
INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (2, "virtual", "weather", "Outside Temperature", "temp_c", "Celsius");


sqlite> select a.rtuid, a.name, s.timestamp, s.value, s.unit from assets a INNER JOIN sensor_data s on a.asset_id = s.asset_id ORDER by s.timestamp;

