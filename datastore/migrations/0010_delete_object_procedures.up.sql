CREATE USER 'delete_objects'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;


CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_site(
    IN auth0id VARCHAR(32), IN strid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'delete'));
    IF allowed THEN
        DELETE FROM arbiter_data.sites WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "delete site"',
        MYSQL_ERRNO = 1142;
    END IF;
END;



CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_observation(
   IN auth0id VARCHAR(32), IN strid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'delete'));
    IF allowed THEN
        DELETE FROM arbiter_data.observations WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "delete observation"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_forecast(
    IN auth0id VARCHAR(32), IN strid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'delete'));
    IF allowed THEN
        DELETE FROM arbiter_data.forecasts WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "delete forecast"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


GRANT DELETE, SELECT (id) ON arbiter_data.sites TO 'delete_objects'@'localhost';
GRANT DELETE, SELECT (id) ON arbiter_data.observations TO 'delete_objects'@'localhost';
GRANT DELETE, SELECT (id) ON arbiter_data.forecasts TO 'delete_objects'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.can_user_perform_action TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_site TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_forecast TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_observation TO 'delete_objects'@'localhost';
