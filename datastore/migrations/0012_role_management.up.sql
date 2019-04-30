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
    SET orgid = (SELECT id from arbiter_data.organizations where name = organization_name);
    INSERT INTO arbiter_data.users (id, auth0_id, organization_id) VALUES (UUID_TO_BIN(strid, 1), auth0id, orgid);
END;

CREATE DEFINER = 'insert_rbac'@'locahost' PROCEDURE create_role (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN name VARCHAR(64),
    IN description VARCHAR(255))
COMMENT 'Create a role'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'roles'));
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

CREATE DEFINER = 'insert_rbac'@'locahost' PROCEDURE create_permission (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN description VARCHAR(255),
    IN action VARCHAR(32), IN object_type VARCHAR(32),
    IN applies_to_all BOOLEAN)
COMMENT 'Create a permission'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET allowed = user_can_create(auth0id, 'roles');
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


CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE add_object_to_permission (
    IN auth0id VARCHAR(32), IN object_id CHAR(36), IN permission_id CHAR(36))
COMMENT 'Add an object to the permission object mapping table'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE objid BINARY(16);
    DECLARE permid BINARY(16);
    SET objid = UUID_TO_BIN(object_id, 1);
    SET permid = UUID_TO_BIN(permission_id, 1);
    SET allowed = can_user_perform_action(auth0id, permid, 'update');
    IF allowed THEN
        INSERT INTO arbiter_data.permission_object_mapping (
            permission_id, object_id) VALUES (objid, permid);
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
    SET roleid = UUID_TO_BIN(role_id, 1);
    SET permid = UUID_TO_BIN(permission_id, 1);
    SET allowed = can_user_perform_action(auth0id, roleid, 'update');
    IF allowed THEN
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
    SET roleid = UUID_TO_BIN(role_id, 1);
    SET userid = UUID_TO_BIN(user_id, 1);
    SET allowed = can_user_perform_action(auth0id, userid, 'update');
    IF allowed THEN
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

/*
add locks to user accounts (update users permission)
add other things
delete user, roles, permissions, remove objs from permission, remove permission from roles, remove roles from user
super super user create organization?
*/
