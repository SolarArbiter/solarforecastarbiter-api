DROP PROCEDURE store_observation_values;
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_observation_values (
    IN auth0id VARCHAR(32), strid CHAR(36), IN data JSON)
COMMENT 'Store a JSON object array with time, value, quality_flag keys into observation_values'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'write_values'));
    IF allowed THEN
        INSERT INTO arbiter_data.observations_values (id, timestamp, value, quality_flag)
            SELECT binid, timestamp, value, quality_flag
            FROM JSON_TABLE(data, '$[*]' COLUMNS (
                timestamp TIMESTAMP PATH '$.timestamp' ERROR ON EMPTY ERROR ON ERROR,
                value FLOAT PATH '$.value' ERROR ON ERROR,
                quality_flag SMALLINT UNSIGNED PATH '$.quality_flag' ERROR ON EMPTY ERROR ON ERROR)
            ) as jsonvals
        ON DUPLICATE KEY UPDATE value=jsonvals.value,
            quality_flag=jsonvals.quality_flag;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "write observation values"',
        MYSQL_ERRNO = 1142;
    END IF;
    select allowed;
END;

GRANT EXECUTE ON PROCEDURE store_observation_values TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE store_observation_values TO 'apiuser'@'%';


DROP PROCEDURE store_forecast_values;
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_forecast_values (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN data JSON)
COMMENT 'Store a JSON object array with timestamp and value keys into forecast_values'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'write_values'));
    IF allowed THEN
        INSERT INTO arbiter_data.forecasts_values (id, timestamp, value)
            SELECT binid, timestamp, value
            FROM JSON_TABLE(data, '$[*]' COLUMNS (
               timestamp TIMESTAMP PATH '$.timestamp' ERROR ON EMPTY ERROR ON ERROR,
               value FLOAT PATH '$.value' ERROR ON ERROR)
            ) as jsonvals
        ON DUPLICATE KEY UPDATE value=jsonvals.value;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "write forecast values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.store_forecast_values TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_forecast_values TO 'apiuser'@'%';


DROP PROCEDURE store_cdf_forecast_values;
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_cdf_forecast_values (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN data JSON)
COMMENT 'Store a JSON object array with timestamp and value keys into cdf_forecast_values'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE groupid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET groupid = (SELECT cdf_forecast_group_id FROM cdf_forecasts_singles WHERE id = binid);
    SET allowed = (SELECT can_user_perform_action(auth0id, groupid, 'write_values'));
    IF allowed THEN
        INSERT INTO arbiter_data.cdf_forecasts_values (id, timestamp, value)
            SELECT binid, timestamp, value
            FROM JSON_TABLE(data, '$[*]' COLUMNS (
                timestamp TIMESTAMP PATH '$.timestamp' ERROR ON EMPTY ERROR ON ERROR,
                value FLOAT PATH '$.value' ERROR ON ERROR)
            ) as jsonvals
        ON DUPLICATE KEY UPDATE value=jsonvals.value;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "write cdf forecast values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.store_cdf_forecast_values TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_cdf_forecast_values TO 'apiuser'@'%';
