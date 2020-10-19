DROP PROCEDURE arbiter_data.update_aggregate;
DROP PROCEDURE arbiter_data.update_site;
DROP PROCEDURE arbiter_data.update_cdf_forecast;
DROP PROCEDURE arbiter_data.update_forecast;
DROP PROCEDURE arbiter_data.update_observation;
ALTER TABLE arbiter_data.observations CHANGE COLUMN uncertainty uncertainty FLOAT NOT NULL;
DROP USER 'update_objects'@'localhost';
