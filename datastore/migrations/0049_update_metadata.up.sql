CREATE USER 'update_objects'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;


CREATE DEFINER = 'update_objects'@'localhost' PROCEDURE update_observation (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN new_name VARCHAR(64), IN new_uncertainty FLOAT,
  IN new_extra_parameters TEXT)
COMMENT 'Update an observation object'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (EXISTS(SELECT 1 FROM arbiter_data.observations where id = binid)
        & can_user_perform_action(auth0id, binid, 'update'));
    IF allowed THEN
        UPDATE arbiter_data.observations SET
           name = COALESCE(new_name, name),
           uncertainty = COALESCE(new_uncertainty, uncertainty),
           extra_parameters = COALESCE(new_extra_parameters, extra_parameters)
        WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "update observation"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON FUNCTION arbiter_data.can_user_perform_action TO 'update_objects'@'localhost';
GRANT UPDATE (name, uncertainty, extra_parameters), SELECT (id, name, uncertainty, extra_parameters) ON arbiter_data.observations TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_observation TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_observation TO 'apiuser'@'%';


CREATE DEFINER = 'update_objects'@'localhost' PROCEDURE update_forecast (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN new_name VARCHAR(64),
  IN new_extra_parameters TEXT)
COMMENT 'Update an forecast object'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (EXISTS(SELECT 1 FROM arbiter_data.forecasts where id = binid)
        & can_user_perform_action(auth0id, binid, 'update'));
    IF allowed THEN
        UPDATE arbiter_data.forecasts SET
           name = COALESCE(new_name, name),
           extra_parameters = COALESCE(new_extra_parameters, extra_parameters)
        WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "update forecast"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT UPDATE (name, extra_parameters), SELECT (id, name, extra_parameters) ON arbiter_data.forecasts TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_forecast TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_forecast TO 'apiuser'@'%';


CREATE DEFINER = 'update_objects'@'localhost' PROCEDURE update_cdf_forecast (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN new_name VARCHAR(64),
  IN new_extra_parameters TEXT)
COMMENT 'Update an cdf forecast group object'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (EXISTS(SELECT 1 FROM arbiter_data.cdf_forecasts_groups where id = binid)
        & can_user_perform_action(auth0id, binid, 'update'));
    IF allowed THEN
        UPDATE arbiter_data.cdf_forecasts_groups SET
           name = COALESCE(new_name, name),
           extra_parameters = COALESCE(new_extra_parameters, extra_parameters)
        WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "update cdf forecast"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT UPDATE (name, extra_parameters), SELECT (id, name, extra_parameters) ON arbiter_data.cdf_forecasts_groups TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_cdf_forecast TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_cdf_forecast TO 'apiuser'@'%';


CREATE DEFINER = 'update_objects'@'localhost' PROCEDURE update_site (
  IN auth0id VARCHAR(32),
  IN strid CHAR(36),
  IN new_name VARCHAR(64),
  IN new_latitude DECIMAL(8, 6),
  IN new_longitude DECIMAL(9, 6),
  IN new_elevation DECIMAL(7, 2),
  IN new_timezone VARCHAR(32),
  IN new_extra_parameters TEXT,
  IN new_ac_capacity DECIMAL(10, 6),
  IN new_dc_capacity DECIMAL(10, 6),
  IN new_temperature_coefficient DECIMAL(7, 5),
  IN new_tracking_type ENUM('fixed', 'single_axis'),
  IN new_surface_tilt DECIMAL(4, 2),
  IN new_surface_azimuth DECIMAL(5, 2),
  IN new_axis_tilt DECIMAL(4, 2),
  IN new_axis_azimuth DECIMAL(5, 2),
  IN new_ground_coverage_ratio DECIMAL(8, 4),
  IN new_backtrack BOOLEAN,
  IN new_max_rotation_angle DECIMAL(5, 2),
  IN new_dc_loss_factor DECIMAL(5, 2),
  IN new_ac_loss_factor DECIMAL(5, 2)
)
COMMENT 'Update a site object'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (EXISTS(SELECT 1 FROM arbiter_data.sites where id = binid)
        & can_user_perform_action(auth0id, binid, 'update'));
    IF allowed THEN
        UPDATE arbiter_data.sites SET
           name = COALESCE(new_name, name),
           latitude = COALESCE(new_latitude, latitude),
           longitude = COALESCE(new_longitude, longitude),
           elevation = COALESCE(new_elevation, elevation),
           timezone = COALESCE(new_timezone, timezone),
           extra_parameters = COALESCE(new_extra_parameters, extra_parameters),
           ac_capacity = COALESCE(new_ac_capacity, ac_capacity),
           dc_capacity = COALESCE(new_dc_capacity, dc_capacity),
           temperature_coefficient = COALESCE(new_temperature_coefficient, temperature_coefficient),
           tracking_type = COALESCE(new_tracking_type, tracking_type),
           surface_tilt = COALESCE(new_surface_tilt, surface_tilt),
           surface_azimuth = COALESCE(new_surface_azimuth, surface_azimuth),
           axis_tilt = COALESCE(new_axis_tilt, axis_tilt),
           axis_azimuth = COALESCE(new_axis_azimuth, axis_azimuth),
           ground_coverage_ratio = COALESCE(new_ground_coverage_ratio, ground_coverage_ratio),
           backtrack = COALESCE(new_backtrack, backtrack),
           max_rotation_angle = COALESCE(new_max_rotation_angle, max_rotation_angle),
           dc_loss_factor = COALESCE(new_dc_loss_factor, dc_loss_factor),
           ac_loss_factor = COALESCE(new_ac_loss_factor, ac_loss_factor)
        WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "update site"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT UPDATE (name, latitude, longitude, elevation, timezone, extra_parameters, ac_capacity, dc_capacity, temperature_coefficient, tracking_type, surface_tilt, surface_azimuth, axis_tilt, axis_azimuth, ground_coverage_ratio, backtrack, max_rotation_angle, dc_loss_factor, ac_loss_factor), SELECT (id, name, latitude, longitude, elevation, timezone, extra_parameters, ac_capacity, dc_capacity, temperature_coefficient, tracking_type, surface_tilt, surface_azimuth, axis_tilt, axis_azimuth, ground_coverage_ratio, backtrack, max_rotation_angle, dc_loss_factor, ac_loss_factor) ON arbiter_data.sites TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_site TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_site TO 'apiuser'@'%';


CREATE DEFINER = 'update_objects'@'localhost' PROCEDURE update_aggregate (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN new_name VARCHAR(64),
  IN new_description VARCHAR(255), IN new_timezone VARCHAR(32),
  IN new_extra_parameters TEXT)
COMMENT 'Update an aggregate object'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (EXISTS(SELECT 1 FROM arbiter_data.aggregates where id = binid)
        & can_user_perform_action(auth0id, binid, 'update'));
    IF allowed THEN
        UPDATE arbiter_data.aggregates SET
           name = COALESCE(new_name, name),
           description = COALESCE(new_description, description),
           timezone = COALESCE(new_timezone, timezone),
           extra_parameters = COALESCE(new_extra_parameters, extra_parameters)
        WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "update aggregate"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT UPDATE (name, description, timezone, extra_parameters), SELECT (id, name, description, timezone, extra_parameters) ON arbiter_data.aggregates TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_aggregate TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_aggregate TO 'apiuser'@'%';
