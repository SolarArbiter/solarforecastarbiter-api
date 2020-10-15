CREATE USER 'update_objects'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;


CREATE DEFINER = 'update_objects'@'localhost' PROCEDURE update_observation (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN new_name VARCHAR(64), IN new_uncertainty FLOAT,
  IN new_extra_parameters TEXT)
COMMENT 'Update an observation object'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (EXISTS(SELECT 1 FROM arbiter_data.observations where id = binid)
        & can_user_perform_action(auth0id, binid, 'update'));
    IF allowed THEN
        UPDATE arbiter_data.observations SET
           name = COALESCE(new_name, name),
           uncertainty = COALESCE(new_uncertainty, uncertainty),
           extra_parameters = COALESCE(new_extra_parameters, extra_parameters)
        WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "update observation"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON FUNCTION arbiter_data.can_user_perform_action TO 'update_objects'@'localhost';
GRANT UPDATE (name, uncertainty, extra_parameters), SELECT (id, name, uncertainty, extra_parameters) ON arbiter_data.observations TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_observation TO 'update_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.update_observation TO 'apiuser'@'%';
