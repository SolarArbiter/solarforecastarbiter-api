CREATE USER 'insert_rbac'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;

-- maybe other users should have create permissions?
CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_user (
   IN strid CHAR(36),
   IN auth0id VARCHAR(32),
   IN organization_name VARCHAR(32))
COMMENT 'Create a user with the given id, auth0 id, and organization'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    SET orgid = get_organization_id(organization_name);
    INSERT INTO arbiter_data.users (id, auth0_id, organization_id) VALUES (UUID_TO_BIN(strid, 1), auth0id, orgid);
END;

CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_role (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN name VARCHAR(64),
    IN description VARCHAR(255))
COMMENT 'Create a role'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET allowed = user_can_create(auth0id, 'roles');
    IF allowed THEN
        SELECT get_user_organization(auth0id) INTO orgid;
        INSERT INTO arbiter_data.roles(
            name, description, id, organization_id) VALUES (
            name, description, UUID_TO_BIN(strid, 1), orgid);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create roles"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_permission (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN description VARCHAR(255),
    IN action VARCHAR(32), IN object_type VARCHAR(32),
    IN applies_to_all BOOLEAN)
COMMENT 'Create a permission'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET allowed = user_can_create(auth0id, 'permissions');
    IF allowed THEN
        SELECT get_user_organization(auth0id) INTO orgid;
        INSERT INTO arbiter_data.permissions(
            id, description, organization_id, action, object_type, applies_to_all
        ) VALUES (
            UUID_TO_BIN(strid, 1), description, orgid, action, object_type,
            applies_to_all);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create permissions"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


-- function to get organization of any rbac object
CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_rbac_object_organization (
    object_id BINARY(16), object_type VARCHAR(32))
RETURNS BINARY(16)
COMMENT 'Return the id of the organization for the rbac object'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    IF object_type = 'users' THEN
        RETURN (SELECT organization_id FROM arbiter_data.users WHERE id = object_id);
    ELSEIF object_type = 'roles' THEN
        RETURN (SELECT organization_id FROM arbiter_data.roles WHERE id = object_id);
    ELSEIF object_type = 'permissions' THEN
        RETURN (SELECT organization_id FROM arbiter_data.permissions WHERE id = object_id);
    ELSE
        RETURN NULL;
    END IF;
END;

GRANT EXECUTE ON FUNCTION arbiter_data.get_rbac_object_organization TO 'select_rbac'@'localhost';

-- function to get organization of any non-rbac object
CREATE DEFINER = 'select_objects'@'localhost' FUNCTION get_nonrbac_object_organization (
    object_id BINARY(16), object_type VARCHAR(32))
RETURNS BINARY(16)
COMMENT 'Return the id of the organization for the object'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    IF object_type = 'sites' THEN
        RETURN (SELECT organization_id FROM arbiter_data.sites WHERE id = object_id);
    ELSEIF object_type = 'observations' THEN
        RETURN (SELECT organization_id FROM arbiter_data.observations WHERE id = object_id);
    ELSEIF object_type = 'forecasts' THEN
        RETURN (SELECT organization_id FROM arbiter_data.forecasts WHERE id = object_id);
    ELSEIF object_type = 'cdf_forecasts' THEN
        RETURN (SELECT organization_id FROM arbiter_data.cdf_forecasts_groups WHERE id = object_id);
    ELSE
        RETURN NULL;
    END IF;
END;

GRANT EXECUTE ON FUNCTION arbiter_data.get_nonrbac_object_organization TO 'select_objects'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_nonrbac_object_organization TO 'select_rbac'@'localhost';


-- function to get organization of any object
CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_object_organization (
    object_id BINARY(16), object_type VARCHAR(32))
RETURNS BINARY(16)
COMMENT 'Return the id of the organization for the object'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    IF object_type in ('users', 'roles', 'permissions') THEN
        RETURN get_rbac_object_organization(object_id, object_type);
    ELSEIF object_type in ('sites', 'observations', 'forecasts', 'cdf_forecasts') THEN
        RETURN get_nonrbac_object_organization(object_id, object_type);
    ELSE
        RETURN NULL;
    END IF;
END;

GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'select_rbac'@'localhost';


CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION is_permission_allowed (
    auth0id VARCHAR(32), permission_id BINARY(16), object_id BINARY(16))
RETURNS BOOLEAN
COMMENT 'Determines if the user is allowed to add the object to the permission'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE userorg BINARY(16);
    DECLARE objtype VARCHAR(32);
    SET userorg = get_user_organization(auth0id);
    SELECT object_type INTO objtype FROM permissions WHERE id = permission_id;
    -- Must be allowed to update permission and read object
    -- and user, permission, object must belong to same org
    -- and object must be same type as described in permission
    SET allowed = can_user_perform_action(auth0id, permission_id, 'update') AND
        can_user_perform_action(auth0id, object_id, 'read') AND
        userorg = get_object_organization(permission_id, 'permissions') AND
        userorg = get_object_organization(object_id, objtype);
    IF allowed IS NOT NULL AND allowed THEN
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;

GRANT EXECUTE ON FUNCTION arbiter_data.is_permission_allowed TO 'select_rbac'@'localhost';


CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE add_object_to_permission (
    IN auth0id VARCHAR(32), IN object_id CHAR(36), IN permission_id CHAR(36))
COMMENT 'Add an object to the permission object mapping table'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE objid BINARY(16);
    DECLARE permid BINARY(16);
    SET objid = UUID_TO_BIN(object_id, 1);
    SET permid = UUID_TO_BIN(permission_id, 1);
    IF is_permission_allowed(auth0id, permid, objid) THEN
        INSERT INTO arbiter_data.permission_object_mapping (
            permission_id, object_id) VALUES (permid, objid);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "add object to permission"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


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


GRANT INSERT ON arbiter_data.users TO 'insert_rbac'@'localhost';
GRANT INSERT ON arbiter_data.user_role_mapping TO 'insert_rbac'@'localhost';
GRANT INSERT ON arbiter_data.roles TO 'insert_rbac'@'localhost';
GRANT INSERT ON arbiter_data.role_permission_mapping TO 'insert_rbac'@'localhost';
GRANT INSERT ON arbiter_data.permissions to 'insert_rbac'@'localhost';
GRANT INSERT ON arbiter_data.permission_object_mapping to 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_user TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_role TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_permission TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_object_to_permission TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_permission_to_role TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_role_to_user TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_organization_id TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.user_can_create TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.can_user_perform_action TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_user_organization TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.is_permission_allowed TO 'insert_rbac'@'localhost';


CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_roles_of_user(userid BINARY(16))
RETURNS JSON
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE jsonout JSON;
    SET jsonout = (SELECT JSON_OBJECTAGG(BIN_TO_UUID(role_id, 1), created_at)
        FROM arbiter_data.user_role_mapping WHERE user_id = userid
        GROUP BY user_id);
    IF jsonout is NOT NULL THEN
        RETURN jsonout;
    ELSE
        RETURN JSON_OBJECT();
    END IF;
END;


CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE read_user(
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read user metadata'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE binid BINARY(16);
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = can_user_perform_action(auth0id, binid, 'read');
    IF allowed THEN
       SELECT BIN_TO_UUID(id, 1) as user_id, auth0_id,
           get_organization_name(organization_id) as organization, created_at, modified_at,
           get_roles_of_user(id) as roles
       FROM arbiter_data.users WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read user"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_permissions_of_role(roleid BINARY(16))
RETURNS JSON
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE jsonout JSON;
    SET jsonout = (SELECT JSON_OBJECTAGG(BIN_TO_UUID(permission_id, 1), created_at)
        FROM arbiter_data.role_permission_mapping WHERE role_id = roleid
        GROUP BY role_id);
    IF jsonout is NOT NULL THEN
        RETURN jsonout;
    ELSE
        RETURN JSON_OBJECT();
    END IF;
END;


CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE read_role(
   IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read role metadata'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE binid BINARY(16);
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = can_user_perform_action(auth0id, binid, 'read');
    IF allowed THEN
       SELECT name, description, BIN_TO_UUID(id, 1) as role_id,
           get_organization_name(organization_id) as organization, created_at, modified_at,
           get_permissions_of_role(id) as permissions
       FROM arbiter_data.roles WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read role"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_permission_objects(permid BINARY(16))
RETURNS JSON
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE jsonout JSON;
    SET jsonout = (SELECT JSON_OBJECTAGG(BIN_TO_UUID(object_id, 1), created_at)
        FROM arbiter_data.permission_object_mapping WHERE permission_id = permid
        GROUP BY permission_id);
    IF jsonout is NOT NULL THEN
        RETURN jsonout;
    ELSE
        RETURN JSON_OBJECT();
    END IF;
END;


CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE read_permission(
   IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read permission metadata'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE binid BINARY(16);
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = can_user_perform_action(auth0id, binid, 'read');
    IF allowed THEN
       SELECT BIN_TO_UUID(id, 1) as permission_id, description,
           get_organization_name(organization_id) as organization, action, object_type, applies_to_all,
           created_at, get_permission_objects(id) as objects
       FROM arbiter_data.permissions WHERE id = binid;
     ELSE
         SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read permission"',
         MYSQL_ERRNO = 1142;
     END IF;
END;


GRANT EXECUTE ON FUNCTION arbiter_data.get_permission_objects TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_permission TO 'select_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_roles_of_user TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_user TO 'select_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_permissions_of_role TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_role TO 'select_rbac'@'localhost';

CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE list_roles (IN auth0id VARCHAR(32))
COMMENT 'List all roles and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT name, description, BIN_TO_UUID(id, 1) as role_id,
    get_organization_name(organization_id) as organization, created_at, modified_at,
    get_permissions_of_role(id) as permissions
FROM roles WHERE id in (
    SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'roles');


CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE list_users (IN auth0id VARCHAR(32))
COMMENT 'List all users and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as user_id, auth0_id,
    get_organization_name(organization_id) as organization, created_at, modified_at,
    get_roles_of_user(id) as roles
FROM users WHERE id in (
    SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'users');


CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE list_permissions (IN auth0id VARCHAR(32))
COMMENT 'List all permissions and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as permission_id, description,
    get_organization_name(organization_id) as organization, action, object_type, applies_to_all,
    created_at, get_permission_objects(id) as objects
FROM permissions WHERE id in (
    SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'permissions');

GRANT SELECT ON arbiter_data.user_objects TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_roles TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_users TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_permissions TO 'select_rbac'@'localhost';


CREATE USER 'delete_rbac'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;

CREATE DEFINER = 'delete_rbac'@'localhost' PROCEDURE delete_role (
    IN auth0id VARCHAR(32), IN strid char(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = can_user_perform_action(auth0id, binid, 'delete');
    IF allowed THEN
        DELETE FROM arbiter_data.roles WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "delete role"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


CREATE DEFINER = 'delete_rbac'@'localhost' PROCEDURE delete_permission (
    IN auth0id VARCHAR(32), IN strid char(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = can_user_perform_action(auth0id, binid, 'delete');
    IF allowed THEN
       DELETE FROM arbiter_data.permissions WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "delete permission"',
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


CREATE DEFINER = 'delete_rbac'@'localhost' PROCEDURE remove_permission_from_role(
    IN auth0id VARCHAR(32), IN permissionid CHAR(36), IN roleid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE rid BINARY(16);
    DECLARE permid BINARY(16);
    DECLARE userorg BINARY(16);
    SET userorg = get_user_organization(auth0id);
    SET rid = UUID_TO_BIN(roleid, 1);
    SET permid = UUID_TO_BIN(permissionid, 1);
    -- Check if user has update permission on the role and that
    -- user and role must be in same org
    SET allowed = can_user_perform_action(auth0id, rid, 'update') AND
        userorg = get_object_organization(rid, 'roles');
    IF allowed IS NOT NULL AND allowed THEN
        DELETE FROM arbiter_data.role_permission_mapping WHERE role_id = rid AND
            permission_id = permid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "remove permission from role"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


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
    SET allowed = can_user_perform_action(auth0id, permid, 'update') AND
        userorg = get_object_organization(permid, 'permissions');
    IF allowed IS NOT NULL AND allowed THEN
        DELETE FROM arbiter_data.permission_object_mapping WHERE object_id = objid AND
            permission_id = permid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "remove object from permission"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


GRANT DELETE, SELECT (id) ON arbiter_data.roles TO 'delete_rbac'@'localhost';
GRANT DELETE, SELECT (id) ON arbiter_data.permissions to 'delete_rbac'@'localhost';
GRANT DELETE, SELECT ON arbiter_data.user_role_mapping TO 'delete_rbac'@'localhost';
GRANT DELETE, SELECT ON arbiter_data.role_permission_mapping TO 'delete_rbac'@'localhost';
GRANT DELETE, SELECT ON arbiter_data.permission_object_mapping to 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_role TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_permission TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.can_user_perform_action TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_object_from_permission TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_permission_from_role TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_role_from_user TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_user_organization TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'delete_rbac'@'localhost';
