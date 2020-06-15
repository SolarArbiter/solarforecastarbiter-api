CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE find_unflagged_observation_dates (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP,
    IN flag SMALLINT UNSIGNED, IN tz VARCHAR(64))
COMMENT 'Find all days (in TZ) where data is not flagged with FLAG'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = is_read_observation_values_allowed(auth0id, binid);
    IF allowed THEN
        SELECT DISTINCT(DATE(CONVERT_TZ(timestamp, 'UTC', tz))) as date
        FROM arbiter_data.observations_values WHERE id = binid AND timestamp BETWEEN start AND end
        AND (quality_flag & flag) != flag;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "find unflagged observation dates"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE find_unflagged_observation_dates TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE find_unflagged_observation_dates TO 'apiuser'@'%';


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE find_observation_gaps (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP
)
COMMENT 'Find the gaps in observation values based on interval_length'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE il INT;
    DECLARE allowed BOOLEAN DEFAULT FALSE;

    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT is_read_observation_values_allowed(auth0id, binid)
                      AND can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
        SET il = (SELECT interval_length FROM arbiter_data.observations WHERE id = binid);
        SELECT j.timestamp, j.next_timestamp AS next_timestamp FROM (
            SELECT timestamp,
                 TIMESTAMPDIFF(MINUTE, timestamp, LEAD(timestamp, 1) OVER w) AS 'diff',
                 LEAD(timestamp, 1) OVER w AS 'next_timestamp'
            FROM arbiter_data.observations_values WHERE id = binid
            AND timestamp BETWEEN start and end WINDOW w AS (ORDER BY timestamp ASC)
        ) AS j WHERE j.diff > il;
    ELSE
         SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "find observation gaps"',
         MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE find_observation_gaps TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE find_observation_gaps TO 'apiuser'@'%';


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE find_forecast_gaps (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP
)
COMMENT 'Find the gaps in forecast values based on interval_length'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE il INT;
    DECLARE allowed BOOLEAN DEFAULT FALSE;

    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT is_read_forecast_values_allowed(auth0id, binid)
                      AND can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
        SET il = (SELECT interval_length FROM arbiter_data.forecasts WHERE id = binid);
        SELECT j.timestamp, j.next_timestamp AS next_timestamp FROM (
            SELECT timestamp,
                 TIMESTAMPDIFF(MINUTE, timestamp, LEAD(timestamp, 1) OVER w) AS 'diff',
                 LEAD(timestamp, 1) OVER w AS 'next_timestamp'
            FROM arbiter_data.forecasts_values WHERE id = binid
            AND timestamp BETWEEN start and end WINDOW w AS (ORDER BY timestamp ASC)
        ) AS j WHERE j.diff > il;
    ELSE
         SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "find forecast gaps"',
         MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE find_forecast_gaps TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE find_forecast_gaps TO 'apiuser'@'%';

-- same for cdf single


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE find_cdf_forecast_gaps (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP
)
COMMENT 'Find the maximum gaps between all forecast values in a CDF group'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE il INT;
    DECLARE allowed BOOLEAN DEFAULT FALSE;

    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read_values')
                      AND can_user_perform_action(auth0id, binid, 'read')
                      AND EXISTS(SELECT 1 FROM arbiter_data.cdf_forecasts_groups WHERE id = binid)
                   );
    IF allowed THEN
        SET il = (SELECT interval_length FROM arbiter_data.cdf_forecasts_groups WHERE id = binid);
        SELECT j.timestamp, MAX(j.next_timestamp) as next_timestamp FROM (
            SELECT timestamp,
                 TIMESTAMPDIFF(MINUTE, timestamp, LEAD(timestamp, 1) OVER w) AS 'diff',
                 LEAD(timestamp, 1) OVER w AS 'next_timestamp'
            FROM arbiter_data.cdf_forecasts_values WHERE id IN (
                 SELECT id FROM arbiter_data.cdf_forecasts_singles WHERE cdf_forecast_group_id = binid
             )
            AND timestamp BETWEEN start and end WINDOW w AS (ORDER BY timestamp ASC)
        ) AS j WHERE j.diff > il  GROUP BY j.timestamp;
    ELSE
         SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "find cdf forecast gaps"',
         MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE find_cdf_forecast_gaps TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE find_cdf_forecast_gaps TO 'apiuser'@'%';


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE find_cdf_single_forecast_gaps (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP
)
COMMENT 'Find the gaps in CDF forecast values based on interval_length'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE groupid BINARY(16);
    DECLARE il INT;
    DECLARE allowed BOOLEAN DEFAULT FALSE;

    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET groupid = (SELECT cdf_forecast_group_id FROM arbiter_data.cdf_forecasts_singles WHERE id = binid);
    SET allowed = (SELECT can_user_perform_action(auth0id, groupid, 'read_values')
                      AND can_user_perform_action(auth0id, groupid, 'read'));
    IF allowed THEN
        SET il = (SELECT interval_length FROM arbiter_data.cdf_forecasts_groups WHERE id = groupid);
        SELECT j.timestamp, j.next_timestamp AS next_timestamp FROM (
            SELECT timestamp,
                 TIMESTAMPDIFF(MINUTE, timestamp, LEAD(timestamp, 1) OVER w) AS 'diff',
                 LEAD(timestamp, 1) OVER w AS 'next_timestamp'
            FROM arbiter_data.cdf_forecasts_values WHERE id = binid
            AND timestamp BETWEEN start and end WINDOW w AS (ORDER BY timestamp ASC)
        ) AS j WHERE j.diff > il;
    ELSE
         SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "find cdf single forecast gaps"',
         MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE find_cdf_single_forecast_gaps TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE find_cdf_single_forecast_gaps TO 'apiuser'@'%';
