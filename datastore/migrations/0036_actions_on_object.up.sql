CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE get_user_actions_on_object(
    IN auth0id VARCHAR(32), IN strobjectid CHAR(36))
COMMENT 'Get a list of all of the actions the user can take on an object.'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE userid BINARY(16);
    DECLARE objectid BINARY(16);
    SET userid = (SELECT id FROM users WHERE auth0_id = auth0id);
    SET objectid = UUID_TO_BIN(strobjectid, 1);
    
    SELECT perm.action from permissions as perm WHERE perm.id IN(
        SELECT permission_id from permission_object_mapping
            WHERE object_id = objectid AND permission_id IN (
                SELECT permission_id FROM role_permission_mapping
                    WHERE role_id IN(
                        SELECT role_id FROM user_role_mapping
                            WHERE user_id = userid
                )
        )
    );
END;

GRANT EXECUTE ON PROCEDURE get_user_actions_on_object TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE get_user_actions_on_object TO 'apiuser'@'%';
