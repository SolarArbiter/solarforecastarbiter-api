CREATE VIEW user_objects AS
SELECT users.auth0_id as auth0_id, pom.object_id as object_id, permissions.object_type as object_type FROM permission_object_mapping as pom, users, permissions WHERE pom.permission_id IN (
    SELECT permission_id FROM role_permission_mapping WHERE role_id IN (
        SELECT role_id FROM user_role_mapping WHERE user_id = users.id
    )
) AND pom.permission_id = permissions.id AND permissions.action = 'read';


CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE list_roles (IN auth0id VARCHAR(32))
COMMENT 'List all roles and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT * FROM roles WHERE id in (
       SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'roles');


CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE list_users (IN auth0id VARCHAR(32))
COMMENT 'List all users and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT * FROM users WHERE id in (
    SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'users');


CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE list_permissions (IN auth0id VARCHAR(32))
COMMENT 'List all permissions and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT * FROM permissions WHERE id in (
       SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'permissions');

-- select_rbac needs to view user_objects to be able to list rbac objects
GRANT SELECT ON arbiter_data.user_objects TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_roles TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_users TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_permissions TO 'select_rbac'@'localhost';


-- create user for selecting non rbac objects with no access to rbac tables
CREATE USER 'select_objects'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;


-- Create procedure to return list of sites a user can read
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_sites (IN auth0id VARCHAR(32))
COMMENT 'List all sites and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as site_id, get_organization_name(organization_id) as provider,
    name, latitude, longitude, elevation, timezone, extra_parameters, ac_capacity, dc_capacity,
    temperature_coefficient, tracking_type, surface_tilt, surface_azimuth, axis_tilt,
    axis_azimuth, ground_coverage_ratio, backtrack, max_rotation_angle,
    dc_loss_factor, ac_loss_factor, created_at, modified_at
FROM sites WHERE id in (
    SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'sites');


-- Create procedure to return list of forecasts a user can read
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_forecasts (IN auth0id VARCHAR(32))
COMMENT 'List all forecasts and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as forecast_id, get_organization_name(organization_id) as provider,
    BIN_TO_UUID(site_id, 1) as site_id, name, variable, issue_time_of_day, lead_time_to_start,
    interval_label, interval_length, run_length, interval_value_type, extra_parameters,
    created_at, modified_at
FROM forecasts WHERE id in (
   SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'forecasts');


-- Create procedure to return list of observations a user can read
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_observations (IN auth0id VARCHAR(32))
COMMENT 'List all observations and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as observation_id, get_organization_name(organization_id) as provider,
    BIN_TO_UUID(site_id, 1) as site_id, name, variable, interval_label, interval_length, interval_value_type,
    uncertainty, extra_parameters, created_at, modified_at
FROM observations WHERE id in (
    SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'observations');


GRANT SELECT ON arbiter_data.user_objects to 'select_objects'@'localhost';
GRANT SELECT ON arbiter_data.sites to 'select_objects'@'localhost';
GRANT SELECT ON arbiter_data.forecasts to 'select_objects'@'localhost';
GRANT SELECT ON arbiter_data.observations to 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_sites to 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_forecasts to 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_observations to 'select_objects'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_organization_name to 'select_objects'@'localhost';
