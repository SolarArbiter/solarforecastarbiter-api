DROP PROCEDURE delete_cdf_forecasts_single;
DROP PROCEDURE delete_cdf_forecasts_group;
DROP PROCEDURE store_cdf_forecast_values;
DROP PROCEDURE store_cdf_forecasts_single;
DROP PROCEDURE store_cdf_forecasts_group;
DROP PROCEDURE read_cdf_forecast_values;
DROP PROCEDURE read_cdf_forecasts_single;
DROP PROCEDURE read_cdf_forecasts_group;
DROP PROCEDURE list_cdf_forecasts_singles;
DROP PROCEDURE list_cdf_forecasts_groups;
DROP FUNCTION get_constant_values;
DROP TRIGGER limit_cdf_forecasts_groups_update;
DROP TRIGGER limit_cdf_forecasts_singles_update;
DROP TRIGGER add_object_perm_on_cdf_forecasts_groups_insert;
DROP TRIGGER add_object_perm_on_cdf_permissions_insert;
REVOKE SELECT, TRIGGER ON arbiter_data.cdf_forecasts_singles FROM 'permission_trig'@'localhost';
REVOKE SELECT, TRIGGER ON arbiter_data.cdf_forecasts_groups FROM 'permission_trig'@'localhost';
ALTER TABLE arbiter_data.permissions CHANGE COLUMN object_type object_type ENUM('sites', 'aggregates', 'forecasts', 'observations', 'users', 'roles', 'permissions') NOT NULL;
DROP TABLE cdf_forecasts_values;
DROP TABLE cdf_forecasts_singles;
DROP TABLE cdf_forecasts_groups;
