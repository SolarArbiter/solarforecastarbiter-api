DROP PROCEDURE read_observation_values;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_observation_values (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP)
COMMENT 'Read observation values'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = is_read_observation_values_allowed(auth0id, binid);
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as observation_id, timestamp, value, quality_flag
        FROM arbiter_data.observations_values WHERE id = binid AND timestamp BETWEEN start AND end;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read observation values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.read_observation_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_observation_values TO 'apiuser'@'%';

DROP PROCEDURE read_forecast_values;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_forecast_values (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP)
COMMENT 'Read forecast values metadata'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = is_read_forecast_values_allowed(auth0id, binid);
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as forecast_id, timestamp, value
        FROM arbiter_data.forecasts_values WHERE id = binid AND timestamp BETWEEN start AND end;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read forecast values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.read_forecast_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_forecast_values TO 'apiuser'@'%';
