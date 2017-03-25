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
INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (1, "RTU1", "ResTemp", "Reservoir Temperature", "res1tmp", "Celsius");
INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (5, "RTU1", "Light", "Light Level", "54", "Lux");
INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (2, "virtual", "weather", "Outside Temperature", "temp_c", "Celsius");
INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (3, "virtual", "weather", "Relative Humidity", "relative_humidity", "%");
INSERT INTO assets (asset_id, rtuid, abbreviation, name, pin, unit) VALUES (4, "virtual", "weather", "Barometric Pressure", "pressure_mb", "mb");
