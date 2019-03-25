CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_site (
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read site metadata'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as id, BIN_TO_UUID(organization_id, 1) as organization_id,
               name, latitude, longitude, elevation, timezone, extra_parameters, ac_capacity,
               dc_capacity, temperature_coefficient, tracking_type, surface_tilt, surface_azimuth,
               axis_tilt, axis_azimuth, ground_coverage_ratio, backtrack, max_rotation_angle,
               dc_loss_factor, ac_loss_factor, created_at, modified_at
        FROM arbiter_data.sites WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read site"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_observation (
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read observation metadata'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as id, BIN_TO_UUID(organization_id, 1) as organization_id,
               BIN_TO_UUID(site_id, 1) as site_id, name, variable, interval_label, interval_length,
               value_type, uncertainty, extra_parameters, created_at, modified_at
        FROM arbiter_data.observations WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read observation"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_forecast (
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read forecast metadata'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as id, BIN_TO_UUID(organization_id, 1) as organization_id,
               BIN_TO_UUID(site_id, 1) as site_id, name, variable, issue_time_of_day, lead_time_to_start,
               interval_label, interval_length, run_length, value_type, extra_parameters,
               created_at, modified_at
        FROM arbiter_data.forecasts WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read forecast"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_observation_values (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP)
COMMENT 'Read observation values'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as id, timestamp, value, quality_flag
        FROM arbiter_data.observations_values WHERE id = binid AND timestamp BETWEEN start AND end;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read observation values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_forecast_values (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP)
COMMENT 'Read forecast values metadata'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as id, timestamp, value
        FROM arbiter_data.forecast_values WHERE id = binid AND timestamp BETWEEN start AND end;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read forecast values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


GRANT SELECT ON arbiter_data.observations_values TO 'select_objects'@'localhost';
GRANT SELECT ON arbiter_data.forecasts_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.can_user_perform_action TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_site TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_observation TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_forecast TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_observation_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_forecast_values TO 'select_objects'@'localhost';
