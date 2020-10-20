DROP PROCEDURE read_metadata_for_value_write;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_metadata_for_value_write (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN object_type VARCHAR(32), IN start TIMESTAMP)
COMMENT 'Read the necessary metadata/values to allow proper validation of data being written'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE groupid BINARY(16);
    DECLARE il INT;
    DECLARE previous_time TIMESTAMP;
    DECLARE extra TEXT;
    DECLARE is_event BOOLEAN; 
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    IF object_type IN ('observations', 'forecasts') THEN
        SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'write_values'));
    ELSEIF object_type = 'cdf_forecasts' THEN
        SET groupid = (SELECT cdf_forecast_group_id FROM cdf_forecasts_singles WHERE id = binid);
        SET allowed = (SELECT can_user_perform_action(auth0id, groupid, 'write_values'));
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Invalid object_type for "read metadata for value write"',
        MYSQL_ERRNO = 1146;
    END IF;

    IF allowed THEN
        IF object_type = 'observations' THEN
            SELECT interval_length, extra_parameters, variable = 'event' INTO il, extra, is_event FROM arbiter_data.observations WHERE id = binid;
            SET previous_time = (SELECT MAX(timestamp) FROM arbiter_data.observations_values WHERE id = binid AND timestamp < start);
        ELSEIF object_type = 'forecasts' THEN
           SELECT interval_length, extra_parameters, variable = 'event' INTO il, extra, is_event FROM arbiter_data.forecasts WHERE id = binid;
            SET previous_time = (SELECT MAX(timestamp) FROM arbiter_data.forecasts_values WHERE id = binid AND timestamp < start);
        ELSEIF object_type = 'cdf_forecasts' THEN
            SELECT interval_length, extra_parameters, variable = 'event' INTO il, extra, is_event FROM arbiter_data.cdf_forecasts_groups WHERE id = groupid;
            SET previous_time = (SELECT MAX(timestamp) FROM arbiter_data.cdf_forecasts_values WHERE id = binid AND timestamp < start);
        END IF;
        IF ISNULL(il) THEN
            -- interval length will only be null if the object doesn't actually exist in the proper table
            SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read metadata for value write"',
            MYSQL_ERRNO = 1142;
        END IF;            
        SELECT il as interval_length, previous_time, extra as extra_parameters, is_event;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read metadata for value write"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE read_metadata_for_value_write TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE read_metadata_for_value_write TO 'apiuser'@'%';
