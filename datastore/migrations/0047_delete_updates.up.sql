DROP PROCEDURE remove_object_from_permission;

CREATE DEFINER = 'delete_rbac'@'localhost' PROCEDURE remove_object_from_permission (
    IN auth0id VARCHAR(32), IN objectid CHAR(36), IN permissionid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE objid BINARY(16);
    DECLARE permid BINARY(16);
    DECLARE userorg BINARY(16);
    SET userorg = get_user_organization(auth0id);
    SET objid = UUID_TO_BIN(objectid, 1);
    SET permid = UUID_TO_BIN(permissionid, 1);
    SET allowed = (can_user_perform_action(auth0id, permid, 'update') AND
        (userorg = get_object_organization(permid, 'permissions')) AND
        EXISTS(
            SELECT 1 FROM arbiter_data.permissions WHERE id = permid AND
            applies_to_all = 0
        ));
    IF allowed IS NOT NULL AND allowed THEN
        DELETE FROM arbiter_data.permission_object_mapping WHERE object_id = objid AND
        permission_id = permid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "remove object from permission"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.remove_object_from_permission TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_object_from_permission TO 'apiuser'@'%';
GRANT SELECT (id, applies_to_all) ON arbiter_data.permissions TO 'delete_rbac'@'localhost';
