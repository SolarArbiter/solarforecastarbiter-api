CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE read_user_id (
    IN auth0id VARCHAR(32), IN user_auth0id VARCHAR(32))
COMMENT 'Return the user_id for a given auth0 ID'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE caller_id BINARY(16);
    DECLARE target_id BINARY(16);
    SET caller_id = (SELECT id FROM arbiter_data.users WHERE auth0_id = auth0id);
    SET target_id = (SELECT id FROM arbiter_data.users WHERE auth0_id = user_auth0id);
    SET allowed = user_org_accepted_tou(caller_id) AND user_org_accepted_tou(target_id);
    IF allowed THEN
        SELECT BIN_TO_UUID(target_id, 1);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read user id"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE read_user_id TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE read_user_id TO 'apiuser'@'%';
