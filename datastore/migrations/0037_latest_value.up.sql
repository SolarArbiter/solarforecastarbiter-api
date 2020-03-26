CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_latest_observation_value (
IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read latest observation value'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE lasttime TIMESTAMP;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read_values'));
    IF allowed THEN
        /* more efficient to set the max time then select one row w/ full index
           vs doing a sort by timestamp desc which has to do a reverse index scan */
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
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read_values'));
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
    DECLARE groupid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET groupid = (SELECT cdf_forecast_group_id FROM cdf_forecasts_singles WHERE id = binid);
    SET allowed = (SELECT can_user_perform_action(auth0id, groupid, 'read_values'));   IF allowed THEN
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
