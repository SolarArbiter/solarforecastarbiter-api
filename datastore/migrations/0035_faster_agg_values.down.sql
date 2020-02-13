DROP PROCEDURE read_aggregate_values;

CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_aggregate_values (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP)
COMMENT 'Read the observation values of the observations that make up the aggregate'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE maxend TIMESTAMP DEFAULT TIMESTAMP('2038-01-19 03:14:07');
    DECLARE minstart TIMESTAMP DEFAULT TIMESTAMP('1970-01-01 00:00:01');
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read_values'));
    IF allowed THEN
        -- In the future, this may be more complex, checking an aggregate_values table first
        -- before retrieving the individual observation objects
        WITH limits AS (
            SELECT observation_id, IFNULL(effective_from, minstart) as obs_start,
                LEAST(IFNULL(effective_until, maxend),
                      IFNULL(observation_deleted_at, maxend)) as obs_end
            FROM arbiter_data.aggregate_observation_mapping
            WHERE aggregate_id = binid AND can_user_perform_action(auth0id, observation_id, 'read_values')
        )
        SELECT BIN_TO_UUID(id, 1) as observation_id, timestamp, value, quality_flag
        FROM arbiter_data.observations_values JOIN limits
        WHERE id = limits.observation_id AND timestamp BETWEEN GREATEST(limits.obs_start, start) AND LEAST(limits.obs_end, end)
        GROUP BY id, timestamp ORDER BY id, timestamp;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read aggregate values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE read_aggregate_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE read_aggregate_values TO 'apiuser'@'%';
