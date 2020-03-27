CREATE DEFINER = 'select_objects'@'localhost' FUNCTION is_read_observation_values_allowed(
  auth0id VARCHAR(32), binid BINARY(16))
RETURNS BOOLEAN
READS SQL DATA SQL SECURITY DEFINER
RETURN (
    EXISTS(SELECT 1 FROM arbiter_data.observations WHERE id = binid) &
    can_user_perform_action(auth0id, binid, 'read_values')
);


CREATE DEFINER = 'select_objects'@'localhost' FUNCTION is_read_forecast_values_allowed(
    auth0id VARCHAR(32), binid BINARY(16))
RETURNS BOOLEAN
READS SQL DATA SQL SECURITY DEFINER
RETURN (
    EXISTS(SELECT 1 FROM arbiter_data.forecasts WHERE id = binid) &
    can_user_perform_action(auth0id, binid, 'read_values')
);


CREATE DEFINER = 'select_objects'@'localhost' FUNCTION is_read_cdf_forecast_values_allowed(
    auth0id VARCHAR(32), binid BINARY(16))
RETURNS BOOLEAN
READS SQL DATA SQL SECURITY DEFINER
/* if groupid is null (no cdf singe) can_user_perform_action will be false */
RETURN can_user_perform_action(auth0id, (SELECT cdf_forecast_group_id FROM cdf_forecasts_singles WHERE id = binid), 'read_values');


GRANT EXECUTE ON FUNCTION is_read_observation_values_allowed TO 'select_objects'@'localhost';
GRANT EXECUTE ON FUNCTION is_read_forecast_values_allowed TO 'select_objects'@'localhost';
GRANT EXECUTE ON FUNCTION is_read_cdf_forecast_values_allowed TO 'select_objects'@'localhost';


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_latest_observation_value (
IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read latest observation value'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE lasttime TIMESTAMP;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = is_read_observation_values_allowed(auth0id, binid);
    IF allowed THEN
        /* more efficient to set the max time then select one row w/ full index
           vs doing a sort by timestamp desc which has to do a reverse index scan
           max/min could probably be functions, but seem unlikely to be used elsewhere
           */
        SET lasttime = (SELECT MAX(timestamp) from arbiter_data.observations_values WHERE id = binid);
        SELECT BIN_TO_UUID(id, 1) as observation_id, timestamp, value, quality_flag
        FROM arbiter_data.observations_values WHERE id = binid AND timestamp = lasttime;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read latest observation value"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_latest_forecast_value (
IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read latest forecast value'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE lasttime TIMESTAMP;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = is_read_forecast_values_allowed(auth0id, binid);
    IF allowed THEN
        SET lasttime = (SELECT MAX(timestamp) from arbiter_data.forecasts_values WHERE id = binid);
        SELECT BIN_TO_UUID(id, 1) as forecast_id, timestamp, value
        FROM arbiter_data.forecasts_values WHERE id = binid AND timestamp = lasttime;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read latest forecast value"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_latest_cdf_forecast_value (
IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read latest cdf forecast value'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE lasttime TIMESTAMP;
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = is_read_cdf_forecast_values_allowed(auth0id, binid);
    IF allowed THEN
        SET lasttime = (SELECT MAX(timestamp) from arbiter_data.cdf_forecasts_values WHERE id = binid);
        SELECT BIN_TO_UUID(id, 1) as forecast_id, timestamp, value
        FROM arbiter_data.cdf_forecasts_values WHERE id = binid AND timestamp = lasttime;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read latest cdf forecast value"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


GRANT EXECUTE ON PROCEDURE arbiter_data.read_latest_observation_value TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_latest_forecast_value TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_latest_cdf_forecast_value TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_latest_observation_value TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_latest_forecast_value TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_latest_cdf_forecast_value TO 'apiuser'@'%';


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_observation_time_range(
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Get observation value time range'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE firsttime TIMESTAMP;
    DECLARE lasttime TIMESTAMP;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = is_read_observation_values_allowed(auth0id, binid);
    IF allowed THEN
        SET lasttime = (SELECT MAX(timestamp) from arbiter_data.observations_values WHERE id = binid);
        SET firsttime = (SELECT MIN(timestamp) from arbiter_data.observations_values WHERE id = binid);
        SELECT firsttime as min_timestamp, lasttime as max_timestamp;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read observation time range"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.read_observation_time_range TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_observation_time_range TO 'apiuser'@'%';


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_forecast_time_range(
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Get forecast value time range'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE firsttime TIMESTAMP;
    DECLARE lasttime TIMESTAMP;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = is_read_forecast_values_allowed(auth0id, binid);
    IF allowed THEN
        SET lasttime = (SELECT MAX(timestamp) from arbiter_data.forecasts_values WHERE id = binid);
        SET firsttime = (SELECT MIN(timestamp) from arbiter_data.forecasts_values WHERE id = binid);
        SELECT firsttime as min_timestamp, lasttime as max_timestamp;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read forecast time range"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.read_forecast_time_range TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_forecast_time_range TO 'apiuser'@'%';



CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_cdf_forecast_time_range(
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Get cdf_forecast value time range'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE firsttime TIMESTAMP;
    DECLARE lasttime TIMESTAMP;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = is_read_cdf_forecast_values_allowed(auth0id, binid);
    IF allowed THEN
        SET lasttime = (SELECT MAX(timestamp) from arbiter_data.cdf_forecasts_values WHERE id = binid);
        SET firsttime = (SELECT MIN(timestamp) from arbiter_data.cdf_forecasts_values WHERE id = binid);
        SELECT firsttime as min_timestamp, lasttime as max_timestamp;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read cdf forecast time range"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.read_cdf_forecast_time_range TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_cdf_forecast_time_range TO 'apiuser'@'%';
