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
    DECLARE limits JSON;

    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read_values'));
    IF allowed THEN
        -- faster than using a cursor as that would require a temporary table
        SET limits = (SELECT JSON_ARRAYAGG(
            JSON_OBJECT('obsid', BIN_TO_UUID(observation_id, 1),
                        'obs_start', GREATEST(IFNULL(effective_from, minstart), start),
                        'obs_end', LEAST(IFNULL(effective_until, maxend),
                                         IFNULL(observation_deleted_at, maxend),
                                         end)))
            FROM arbiter_data.aggregate_observation_mapping
            WHERE aggregate_id = binid AND can_user_perform_action(auth0id, observation_id, 'read_values'));

         SELECT jt.obsid as observation_id, timestamp, value, quality_flag
         FROM arbiter_data.observations_values, JSON_TABLE(limits, '$[*]' COLUMNS (
             obsid char(36) PATH '$.obsid', obs_start TIMESTAMP PATH '$.obs_start',
             obs_end TIMESTAMP PATH '$.obs_end')) as jt
         WHERE id = UUID_TO_BIN(jt.obsid, 1) AND timestamp BETWEEN jt.obs_start AND jt.obs_end;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read aggregate values"',
        MYSQL_ERRNO = 1142;
    END IF;
END ;

GRANT EXECUTE ON PROCEDURE read_aggregate_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE read_aggregate_values TO 'apiuser'@'%';
