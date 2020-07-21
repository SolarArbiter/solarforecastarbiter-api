CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE site_has_modeling_parameters (
    IN auth0id VARCHAR(32), IN siteid CHAR(36))
COMMENT 'Check for modeling parameters on a site'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE canreadsite BOOLEAN DEFAULT FALSE;


    SET binid = UUID_TO_BIN(siteid, 1);
    SET canreadsite = (SELECT can_user_perform_action(auth0id, binid, 'read'));

    IF canreadsite THEN
        SELECT NOT ISNULL(tracking_type)
        FROM sites
        WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not have permission to read site', MYSQL_ERRNO = 1143;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.site_has_modeling_parameters TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.site_has_modeling_parameters TO 'apiuser'@'%';
