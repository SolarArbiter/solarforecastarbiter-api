CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_observation_from_aggregate(
    IN auth0id VARCHAR(32), IN agg_strid CHAR(36), IN obs_strid CHAR(36))
COMMENT 'Deletes an observation to an aggregate object'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binaggid BINARY(16);
    DECLARE binobsid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binaggid = UUID_TO_BIN(agg_strid, 1);
    SET binobsid = UUID_TO_BIN(obs_strid, 1);
    SET allowed = (SELECT can_user_perform_action(auth0id, binaggid, 'update'));
    IF allowed THEN
        DELETE FROM arbiter_data.aggregate_observation_mapping WHERE aggregate_id = binaggid AND observation_id = binobsid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "delete observation from aggregate"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT DELETE, SELECT(aggregate_id, observation_id) ON arbiter_data.aggregate_observation_mapping TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE delete_observation_from_aggregate TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE delete_observation_from_aggregate TO 'apiuser'@'%';
