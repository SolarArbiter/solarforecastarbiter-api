CREATE USER 'insert_objects'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;


CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_site (
    IN auth0id VARCHAR(32), IN strid CHAR(36),
    IN name VARCHAR(64), IN latitude DECIMAL(8, 6), IN longitude DECIMAL(9, 6),
    IN elevation DECIMAL(7, 2), IN timezone VARCHAR(32), IN extra_parameters TEXT,
    IN ac_capacity DECIMAL(10, 6), IN dc_capacity DECIMAL(10, 6),
    IN temperature_coefficient DECIMAL(7, 5), IN tracking_type VARCHAR(32),
    IN surface_tilt DECIMAL(4, 2), IN surface_azimuth DECIMAL(5, 2),
    IN axis_tilt DECIMAL(4, 2), IN axis_azimuth DECIMAL(5, 2),
    IN ground_coverage_ratio DECIMAL(8, 4), IN backtrack BOOLEAN,
    IN max_rotation_angle DECIMAL(5, 2), IN dc_loss_factor DECIMAL(5, 2),
    IN ac_loss_factor DECIMAL(5, 2))
COMMENT 'Store an observation object. User must be able to read site information.'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'sites'));
    IF allowed THEN
        SELECT organization_id INTO orgid FROM arbiter_data.users WHERE auth0_id = auth0id;
        INSERT INTO arbiter_data.sites (
            id, organization_id, name, latitude, longitude, elevation, timezone, extra_parameters,
            ac_capacity, dc_capacity, temperature_coefficient, tracking_type, surface_tilt,
            surface_azimuth, axis_tilt, axis_azimuth, ground_coverage_ratio, backtrack,
            max_rotation_angle, dc_loss_factor, ac_loss_factor
         ) VALUES (
             UUID_TO_BIN(strid, 1), orgid, name, latitude, longitude, elevation, timezone, extra_parameters,
             ac_capacity, dc_capacity, temperature_coefficient, tracking_type, surface_tilt,
             surface_azimuth, axis_tilt, axis_azimuth, ground_coverage_ratio, backtrack,
             max_rotation_angle, dc_loss_factor, ac_loss_factor
         );
    ELSE
       SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create sites"',
          MYSQL_ERRNO = 1142;
    END IF;
END;


CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_observation (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN variable VARCHAR(32), IN site_id CHAR(36), IN name VARCHAR(64),
  IN interval_label VARCHAR(32), IN interval_length SMALLINT UNSIGNED, IN value_type VARCHAR(32),
  IN uncertainty FLOAT, IN extra_parameters TEXT)
COMMENT 'Store an observation object. User must be able to read site information.'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE binsiteid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE canreadsite BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'observations'));
    SET binsiteid = (SELECT UUID_TO_BIN(site_id, 1));
    IF allowed THEN
       SET canreadsite = (SELECT can_user_perform_action(auth0id, binsiteid, 'read'));
       IF canreadsite THEN
            SELECT organization_id INTO orgid FROM arbiter_data.users WHERE auth0_id = auth0id;
            INSERT INTO arbiter_data.observations (
                id, organization_id, site_id, name, variable, interval_label, interval_length,
                value_type, uncertainty, extra_parameters
            ) VALUES (
                UUID_TO_BIN(strid, 1), orgid, binsiteid, name, variable, interval_label,
                interval_length, value_type, uncertainty, extra_parameters);
       ELSE
           SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not have permission to read site', MYSQL_ERRNO = 1143;
       END IF;
    ELSE
       SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create observations"',
       MYSQL_ERRNO = 1142;
    END IF;
END;


CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_forecast (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN site_id CHAR(36), IN name VARCHAR(64), IN variable VARCHAR(32),
  IN issue_time_of_day TIME, IN lead_time_to_start SMALLINT UNSIGNED, IN interval_label VARCHAR(32),
  IN interval_length SMALLINT UNSIGNED, IN run_length SMALLINT UNSIGNED, IN value_type VARCHAR(32),
  IN extra_parameters TEXT)
COMMENT 'Store an forecast object. User must be able to read site information.'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE binsiteid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE canreadsite BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'forecasts'));
    SET binsiteid = (SELECT UUID_TO_BIN(site_id, 1));
    IF allowed THEN
       SET canreadsite = (SELECT can_user_perform_action(auth0id, binsiteid, 'read'));
       IF canreadsite THEN
            SELECT organization_id INTO orgid FROM arbiter_data.users WHERE auth0_id = auth0id;
            INSERT INTO arbiter_data.forecasts (
                id, organization_id, site_id, name, variable, issue_time_of_day, lead_time_to_start,
                interval_label, interval_length, run_length, value_type, extra_parameters
            ) VALUES (
                UUID_TO_BIN(strid, 1), orgid, binsiteid, name, variable, issue_time_of_day,
                lead_time_to_start, interval_label, interval_length, run_length, value_type,
                extra_parameters);
       ELSE
           SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not have permission to read site', MYSQL_ERRNO = 1143;
       END IF;
    ELSE
       SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create forecasts"',
       MYSQL_ERRNO = 1142;
    END IF;
END;


GRANT INSERT ON arbiter_data.sites TO 'insert_objects'@'localhost';
GRANT INSERT ON arbiter_data.observations TO 'insert_objects'@'localhost';
GRANT INSERT ON arbiter_data.forecasts TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_site to 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_observation to 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_forecast to 'insert_objects'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.user_can_create TO 'insert_objects'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.can_user_perform_action TO 'insert_objects'@'localhost';
GRANT SELECT ON arbiter_data.users TO 'insert_objects'@'localhost';
