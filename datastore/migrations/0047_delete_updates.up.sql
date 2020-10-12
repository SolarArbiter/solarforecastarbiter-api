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


DROP PROCEDURE delete_user;
CREATE DEFINER = 'delete_rbac'@'localhost' PROCEDURE delete_user(
    IN struserid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE userid BINARY(16);
    SET userid = UUID_TO_BIN(struserid, 1);
    IF EXISTS(SELECT 1 FROM arbiter_data.users WHERE id = userid) THEN
        DELETE FROM arbiter_data.users WHERE id = userid;
        CALL remove_user_facing_permissions_and_default_roles(userid);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not exist',
        MYSQL_ERRNO = 1305;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_user TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_user TO 'frameworkadmin'@'%';


DROP PROCEDURE create_user_if_not_exists;
CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_user_if_not_exists(IN auth0id VARCHAR(32))
COMMENT 'Inserts a new user and adds them to the Unaffiliated org, and read reference role'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE userid BINARY(16);
    IF NOT does_user_exist(auth0id) THEN
        SET userid = UUID_TO_BIN(UUID(), 1);
        INSERT INTO arbiter_data.users (id, auth0_id, organization_id) VALUES (
            userid, auth0id, get_organization_id('Unaffiliated'));
        CALL arbiter_data.add_reference_role_to_user(userid);
        CALL arbiter_data.create_default_user_role(userid, get_organization_id('Unaffiliated'));
        SELECT BIN_TO_UUID(userid, 1) as user_id;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.create_user_if_not_exists TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_user_if_not_exists TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_user_if_not_exists TO 'frameworkadmin'@'%';
