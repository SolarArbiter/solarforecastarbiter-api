ALTER TABLE arbiter_data.permissions CHANGE COLUMN object_type object_type ENUM('sites', 'aggregates', 'cdf_forecasts', 'forecasts', 'observations', 'users', 'roles', 'permissions') NOT NULL;
DROP TABLE report_values;
DROP TABLE reports;
DROP PROCEDURE list_reports;
DROP PROCEDURE read_report;
DROP PROCEDURE store_report;
DROP PROCEDURE store_report_values;
DROP PROCEDURE delete_report;
