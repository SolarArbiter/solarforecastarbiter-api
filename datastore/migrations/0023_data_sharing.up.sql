/*
 *Add role_grants to permissions, role_grants describes creating entries in the
 */
ALTER TABLE arbiter_data.permissions CHANGE COLUMN object_type object_type ENUM('sites', 'aggregates', 'cdf_forecasts', 'forecasts', 'observations', 'users', 'roles', 'permissions', 'reports', 'role_grants') NOT NULL;

/*
 * RBAC helper functions to limit sharing of roles outside the organization.
 */
CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION role_granted_to_external_users(orgid BINARY(16), roleid BINARY(16))
RETURNS BOOLEAN
COMMENT 'Determines if a role has been granted to a user outside the organizaiton'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    RETURN (SELECT EXISTS(
        SELECT 1 FROM arbiter_data.user_role_mapping
            WHERE role_id = roleid
            AND user_id IN (
                SELECT id FROM arbiter_data.users
                WHERE organization_id != orgid
            )
        )
    );
END;
GRANT EXECUTE ON FUNCTION arbiter_data.role_granted_to_external_users TO 'select_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.role_granted_to_external_users TO 'insert_rbac'@'localhost';


CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION role_contains_admin_permissions(roleid BINARY(16))
RETURNS BOOLEAN
COMMENT 'Determines if a role contains rbac object permissions'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    RETURN (SELECT EXISTS (
        SELECT 1 FROM arbiter_data.role_permission_mapping
            WHERE role_id = roleid
            AND permission_id IN (
                SELECT id FROM arbiter_data.permissions
                WHERE object_type IN ('roles', 'permissions', 'role_grants', 'users')
            )
        )
    );
END;
GRANT EXECUTE ON FUNCTION arbiter_data.role_contains_admin_permissions TO 'select_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.role_contains_admin_permissions TO 'insert_rbac'@'localhost';

/*
 * Drop and redefine add_role_to_user dependent on role_grants permission.
 */
DROP PROCEDURE arbiter_data.add_role_to_user;

CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE add_role_to_user (
    IN auth0id VARCHAR(32), IN user_id CHAR(36), IN role_id CHAR(36))
COMMENT 'Add a role to a user'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE roleid BINARY(16);
    DECLARE userid BINARY(16);
    DECLARE role_org BINARY(16);
    DECLARE caller_org BINARY(16);
    DECLARE grantee_org BINARY(16);

    SET roleid = UUID_TO_BIN(role_id, 1);
    SET role_org = get_object_organization(roleid, 'roles');
    SET caller_org = get_user_organization(auth0id);
    SET userid = UUID_TO_BIN(user_id, 1);
    SET grantee_org = (SELECT organization_id FROM arbiter_data.users WHERE id = userid);
    SET allowed = user_can_create(auth0id, 'role_grants') AND
          caller_org = role_org AND
          (SELECT id IS NOT NULL FROM users WHERE id = userid);
    IF allowed THEN
        IF caller_org = grantee_org THEN
            -- If caller and grantee have same org, add the role to the user
            INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (
                userid, roleid);
        ELSE
            IF role_contains_admin_permissions(roleid) THEN
                /* If caller and grantee do not have same org, and the role contains
                 * administrative permissions, return an error.
                 */
                SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Cannot share administrative role outside organization',
                MYSQL_ERRNO = 1142;
            ELSE
                INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (
                    userid, roleid);
            END IF;
        END IF;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "add role to user"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.add_role_to_user TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_role_to_user TO 'apiuser'@'%';
GRANT SELECT ON arbiter_data.users TO 'insert_rbac'@'localhost';

/*
 * Frop delete_role_from user and redefine using the role_grants permission
 */
DROP PROCEDURE remove_role_from_user;

-- define delete role from user
CREATE DEFINER = 'delete_rbac'@'localhost' PROCEDURE remove_role_from_user (
    IN auth0id VARCHAR(32), IN user_strid VARCHAR(36), IN role_strid VARCHAR(36))
COMMENT 'Remove a role from a user'
BEGIN
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE roleid BINARY(16);
    DECLARE role_org BINARY(16);
    DECLARE userid BINARY(16);
    DECLARE caller_org BINARY(16);
    SET caller_org = get_user_organization(auth0id);
    SET roleid = UUID_TO_BIN(role_strid, 1);
    SET role_org = get_object_organization(roleid, 'roles');
    SET userid = UUID_TO_BIN(user_strid, 1);
    -- calling user must have create role_grants
    -- calling user and role must be in the same organization
    SET allowed = user_can_create(auth0id, 'role_grants') AND
         (caller_org = role_org);
    IF allowed THEN
        DELETE FROM arbiter_data.user_role_mapping WHERE user_id = userid AND role_id = roleid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "remove role from user"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_role_from_user TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.user_can_create TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_role_from_user TO 'apiuser'@'%';
GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'delete_rbac'@'localhost';
/*
 * Define the Unaffiliated Organization and the basic user role to read
 * reference data.
 */
SET @orgid = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.organizations (name, id, accepted_tou) VALUES (
        'Unaffiliated', @orgid, FALSE);

/*
 * If the calling user does not exist, create a new user and add them to the
 * database under the 'unaffiliated' org grant them the Reference reading role
 */
CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_user_if_not_exists(IN auth0id VARCHAR(32))
COMMENT 'Inserts a new user and adds then to the Public org, and read reference role'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE userid BINARY(16);
    DECLARE reference_roleid BINARY(16);
    SET userid = UUID_TO_BIN(UUID(), 1);
    SET orgid = (SELECT id FROM arbiter_data.organizations WHERE name = "Unaffiliated");
    SET reference_roleid = (SELECT id FROM arbiter_data.roles WHERE name = 'Read Reference Data');
    IF (SELECT NOT EXISTS(SELECT 1 FROM arbiter_data.users WHERE auth0_id = auth0id)) THEN
        INSERT INTO arbiter_data.users (id, auth0_id, organization_id) VALUES (
            userid, auth0id, orgid);
        INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (userid, reference_roleid);
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.create_user_if_not_exists TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_user_if_not_exists TO 'apiuser'@'%';

/*
 * Procedure to get current user metadata (auth0id, organization name and id)
 */
CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE get_current_user_info (
    IN auth0id VARCHAR(32))
COMMENT 'Read the identifying information for the current user.'
BEGIN
    SELECT get_organization_name(organization_id) as organization,
        BIN_TO_UUID(organization_id, 1) as organization_id,
        BIN_TO_UUID(id, 1) as user_id, auth0_id
    FROM arbiter_data.users WHERE auth0_id = auth0id;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.get_current_user_info TO 'select_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_organization_name TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.get_current_user_info TO 'apiuser'@'%';

/*
 * List users with role in the organization.
 */
CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE list_priveleged_users (
    IN auth0id VARCHAR(32))
COMMENT 'List all users who are granted a role within the organization'
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE allowed BOOLEAN;
    SET allowed = user_can_create(auth0id, 'role_grants');
    IF allowed THEN
        SET orgid = get_user_organization(auth0id);
        SELECT BIN_TO_UUID(id, 1) as user_id, get_organization_name(organization_id) as organization, BIN_TO_UUID(organization_id) as organization_id, auth0_id
        FROM arbiter_data.users
        WHERE id IN (
            SELECT DISTINCT user_id
            FROM arbiter_data.user_role_mapping
            WHERE role_id IN (
                SELECT id
                FROM arbiter_data.roles
                WHERE organization_id = orgid));
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "list_priveleged_users"',
        MYSQL_ERRNO = 1142;
    END IF;

END;
GRANT EXECUTE ON PROCEDURE arbiter_data.list_priveleged_users TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_priveleged_users TO 'apiuser'@'%';
