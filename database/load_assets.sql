INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (1, "RTU1", "ResTemp", "Reservoir Temperature", "res1tmp", "Celsius");
INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (5, "RTU1", "Light", "Light Level", "54", "Lux");
INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (2, "virtual", "weather", "Outside Temperature", "temp_c", "Celsius");
INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (3, "virtual", "weather", "Relative Humidity", "relative_humidity", "%");
INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (4, "virtual", "weather", "Barometric Pressure", "pressure_mb", "mb");

SELECT a.rtuid, a.name, s.timestamp, s.value, s.unit 
FROM assets a INNER JOIN sensor_data s ON a.asset_id = s.asset_id ORDER by s.timestamp;

SELECT a.rtuid, a.name, s.timestamp, s.value, s.unit FROM assets a INNER JOIN sensor_data s ON a.asset_id = s.asset_id WHERE s.unit = 'Lux' ORDER by s.timestamp;

INSERT INTO Site (site_id, name, wunder_key, operator, email, phone, location, longitude, latitude) VALUES ('HAPI01', 'HAPI R&D Facility', 'ffb22aac10a07be6', 'Maya Culpa, LLC', 'info@hapihq.com', '555-5555', 'Columbus, Ohio', '82.9988° W', '39.9612° N');
