ALTER TABLE arbiter_data.permissions CHANGE COLUMN object_type object_type ENUM('sites', 'aggregates', 'cdf_forecasts', 'forecasts', 'observations', 'users', 'roles', 'permissions', 'reports') NOT NULL;

DELETE FROM arbiter_data.organizations WHERE name = 'Unaffiliated';
DROP PROCEDURE add_role_to_user;
DROP FUNCTION rbac_permissions_check;
DROP FUNCTION role_contains_rbac_permissions;
DROP FUNCTION role_granted_to_external_users;
DROP FUNCTION get_user_organization_by_user_id;
DROP FUNCTION get_organization_id_by_name;
DROP FUNCTION get_reference_role_id;
DROP FUNCTION does_user_exist;
DROP PROCEDURE remove_role_from_user;
DROP PROCEDURE create_user_if_not_exists;
DROP PROCEDURE get_current_user_info;
DROP PROCEDURE list_privileged_users;
DROP PROCEDURE user_exists;


CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE add_role_to_user (
    IN auth0id VARCHAR(32), IN user_id CHAR(36), IN role_id CHAR(36))
COMMENT 'Add a role to a user'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE roleid BINARY(16);
    DECLARE userid BINARY(16);
    DECLARE userorg BINARY(16);
    SET userorg = get_user_organization(auth0id);
    SET roleid = UUID_TO_BIN(role_id, 1);
    SET userid = UUID_TO_BIN(user_id, 1);
    -- calling user must have update permission on user and
    -- calling user, user, role must be in same org
    -- add role from outside org is handled separately
    SET allowed = can_user_perform_action(auth0id, userid, 'update') AND
        userorg = get_object_organization(userid, 'users') AND
        userorg = get_object_organization(roleid, 'roles');
    IF allowed IS NOT NULL AND allowed THEN
    INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (
        userid, roleid);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "add permission to role"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

CREATE DEFINER = 'delete_rbac'@'localhost' PROCEDURE remove_role_from_user (
    IN auth0id VARCHAR(32), IN roleid CHAR(36), IN userid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE rid BINARY(16);
    DECLARE uid BINARY(16);
    DECLARE userorg BINARY(16);
    SET rid = UUID_TO_BIN(roleid, 1);
    SET uid = UUID_TO_BIN(userid, 1);
    SET userorg = get_user_organization(auth0id);
    -- calling user must have update permission on user and
    -- calling user and user must be in same org
    SET allowed = can_user_perform_action(auth0id, uid, 'update') AND 
        userorg = get_object_organization(uid, 'users');
    IF allowed IS NOT NULL AND allowed THEN
        DELETE FROM arbiter_data.user_role_mapping WHERE user_id = uid AND role_id = rid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "remove role from user"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_role_from_user TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_role_from_user TO 'apiuser'@'%';

GRANT EXECUTE ON PROCEDURE arbiter_data.add_role_to_user TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_role_to_user TO 'apiuser'@'%';

-- Redefine original add_permission_to_role state
DROP PROCEDURE add_permission_to_role;

CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE add_permission_to_role (
    IN auth0id VARCHAR(32), IN role_id CHAR(36), IN permission_id CHAR(36))
COMMENT 'Add an permission to the role permission mapping table'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE roleid BINARY(16);
    DECLARE permid BINARY(16);
    DECLARE userorg BINARY(16);
    SET userorg = get_user_organization(auth0id);
    SET roleid = UUID_TO_BIN(role_id, 1); 
    SET permid = UUID_TO_BIN(permission_id, 1); 
    -- Check if user has update permission on the role and that
    -- user, role, and permission have same organization
    SET allowed = can_user_perform_action(auth0id, roleid, 'update') AND 
        userorg = get_object_organization(permid, 'permissions') AND 
        userorg = get_object_organization(roleid, 'roles');
    IF allowed IS NOT NULL AND allowed THEN
        INSERT INTO arbiter_data.role_permission_mapping (
            role_id, permission_id) VALUES (roleid, permid);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "add permission to role"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.add_permission_to_role TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_permission_to_role TO 'apiuser'@'%';

DELETE FROM arbiter_data.users WHERE auth0_id = 'auth0|test_public';
