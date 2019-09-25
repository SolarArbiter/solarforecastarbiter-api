/*
 * Establish new mysql user
 */

CREATE USER 'frameworkadmin'@'%' IDENTIFIED BY 'thisisaterribleandpublicpassword';
CREATE USER 'update_rbac'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;

/*
 * Set unique key to the pair of role name, organizaiton id
 */
ALTER TABLE arbiter_data.roles DROP INDEX name;
ALTER TABLE arbiter_data.roles ADD UNIQUE organization_role (name, organization_id);


/*
 * Create an organization
 * Should the default be accepted_tou = true? or 
 * false and manual update
 */
CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_organization (
    IN org_name VARCHAR(32))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    -- set orgid
    DECLARE orgid BINARY(16);
    SET orgid = (SELECT UUID_TO_BIN(UUID(), 1));
    -- insert into organization
    INSERT INTO arbiter_data.organizations(name, id, accepted_tou) VALUES (
        org_name, orgid, FALSE);
    CALL create_default_read_role(orgid);
    CALL create_default_write_role(orgid);
    CALL create_default_create_role(orgid);
    CALL create_default_delete_role(orgid);
    CALL create_default_admin_role(orgid);
END;
GRANT INSERT ON arbiter_data.organizations TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_organization TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_organization TO 'frameworkadmin'@'%';

/*
 * Default role procedures
 */
CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_default_read_role(
    IN orgid BINARY(16))
COMMENT "Role to read all data and metadata within the organization"
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE roleid BINARY(16);
    DECLARE read_sites BINARY(16);
    DECLARE read_obs BINARY(16);
    DECLARE read_obs_values BINARY(16);
    DECLARE read_fx BINARY(16);
    DECLARE read_fx_values BINARY(16);
    DECLARE read_cdf BINARY(16);
    DECLARE read_cdf_values BINARY(16);
    DECLARE read_reports BINARY(16);
    DECLARE read_report_values BINARY(16);
    DECLARE read_agg BINARY(16);
    DECLARE read_agg_values BINARY(16);
    SET roleid = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.roles(
        name, description, id, organization_id) VALUES(
        'Read all', 'View all data and metadata', roleid, orgid);
    -- read all sites
    SET read_sites = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_sites, "Read all sites", orgid, "read", "sites", TRUE);
    -- read all observations
    SET read_obs = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_obs, "Read all observations", orgid, "read", "observations", TRUE);
    -- read_vallues all observations
    SET read_obs_values = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_obs_values, "Read all observation values", orgid, "read_values", "observations", TRUE);
    -- read all forecasts
    SET read_fx = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_fx, "Read all forecasts", orgid, "read", "forecasts", TRUE);
    -- read_values all forecasts
    SET read_fx_values = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_fx_values, "Read all forecast values", orgid, "read_values", "forecasts", TRUE);
    -- read all cdf_forecast_groups
    SET read_cdf = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_cdf, "Read all probabilistic forecasts", orgid, "read", "cdf_forecasts", TRUE);
    -- read_values all cdf_forecast_groups
    SET read_cdf_values = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_cdf_values, "Read all probabilistic forecast values", orgid, "read_values", "cdf_forecasts", TRUE);
    -- read all reports
    SET read_reports = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_reports, "Read all reports", orgid, "read", "reports", TRUE);
    -- read_values all reports
    SET read_report_values = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_report_values, "Read all report values", orgid, "read_values", "reports", TRUE);
    -- read all aggregates
    SET read_agg = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_agg, "Read all aggregates", orgid, "read", "aggregates", TRUE);
    -- read_values all aggregates
    SET read_agg_values = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_agg_values, "Read all aggregate values", orgid, "read_values", "aggregates", TRUE);
    -- add read permissions to the role
    INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (
        roleid, read_sites), (
        roleid, read_obs), (
        roleid, read_obs_values), (
        roleid, read_fx), (
        roleid, read_fx_values), (
        roleid, read_cdf), (
        roleid, read_cdf_values), (
        roleid, read_reports), (
        roleid, read_report_values), (
        roleid, read_agg), (
        roleid, read_agg_values); 
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_read_role TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_read_role TO 'frameworkadmin'@'%';


CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_default_write_role(
    IN orgid BINARY(16))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE roleid BINARY(16);
    DECLARE write_obs BINARY(16);
    DECLARE write_fx BINARY(16);
    DECLARE write_cdf BINARY(16);
    DECLARE write_aggregates BINARY(16);
    DECLARE write_reports BINARY(16);
    -- Write all values
    SET roleid = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.roles(
        name, description, id, organization_id) VALUES(
        'Write all values', 'Allows the user to submit data within the organization', roleid, orgid);
    -- write_values all observations
    SET write_obs = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        write_obs, "Submit values to all observations", orgid, "write_values", "observations", TRUE);
    -- write_values all forecasts
    SET write_fx = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        write_fx, "Submit values to all forecasts", orgid, "write_values", "forecasts", TRUE);
    -- write_values all cdf_forecast_groups
    SET write_cdf = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        write_cdf, "Submit values to all probabilistic forecasts", orgid, "write_values", "cdf_forecasts", TRUE);
    -- write_values all aggregates
    SET write_aggregates = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        write_aggregates, "Submit values to all aggregates", orgid, "write_values", "aggregates", TRUE);
    -- write_values all reports
    SET write_reports = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        write_reports, "Submit values to all reports", orgid, "write_values", "reports", TRUE);
    -- add all write perms to the role
    INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (
        roleid, write_obs), (
        roleid, write_fx), (
        roleid, write_cdf), (
        roleid, write_aggregates), (
        roleid, write_reports);
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_write_role TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_write_role TO 'frameworkadmin'@'%';


CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_default_create_role(
    IN orgid BINARY(16))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    -- parse orgid
    DECLARE roleid BINARY(16);
    DECLARE create_obs BINARY(16);
    DECLARE create_fx BINARY(16);
    DECLARE create_cdf BINARY(16);
    DECLARE create_aggregates BINARY(16);
    DECLARE create_reports BINARY(16);
    DECLARE create_sites BINARY(16);
    -- Create all types of metadata
    SET roleid = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.roles(
        name, description, id, organization_id) VALUES(
        'Create metadata', 'Allows the user to create metadata types', roleid, orgid);
    -- create observations
    SET create_obs = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        create_obs, "Create observations", orgid, "create", "observations", TRUE);
    -- create forecast
    SET create_fx = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        create_fx, "Create forecasts", orgid, "create", "forecasts", TRUE);
    -- crreate cdf forecasts
    
    SET create_cdf = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        create_cdf, "Create probabilistic forecasts", orgid, "create", "cdf_forecasts", TRUE);
    -- create aggregates
    SET create_aggregates = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        create_aggregates, "Create aggregates", orgid, "create", "aggregates", TRUE);
    -- create reports
    SET create_reports = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        create_reports, "Create reports", orgid, "create", "reports", TRUE);
    -- create sites
    SET create_sites = UUID_TO_BIN(UUID(), 1);
     INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        create_sites, "Create sites", orgid, "create", "sites", TRUE);
    -- add all write perms to the role
    INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (
        roleid, create_obs), (
        roleid, create_fx), (
        roleid, create_cdf), (
        roleid, create_aggregates), (
        roleid, create_sites), (
        roleid, create_reports);
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_create_role TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_create_role TO 'frameworkadmin'@'%';


CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_default_delete_role(
    IN orgid BINARY(16))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE roleid BINARY(16);
    DECLARE delete_obs BINARY(16);
    DECLARE delete_fx BINARY(16);
    DECLARE delete_cdf BINARY(16);
    DECLARE delete_aggregates BINARY(16);
    DECLARE delete_reports BINARY(16);
    DECLARE delete_sites BINARY(16);
    -- Delete all types of metadata
    SET roleid = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.roles(
        name, description, id, organization_id) VALUES(
        'Delete metadata', 'Allows the user to delete metadata', roleid, orgid);
    -- delete observations
    SET delete_obs = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        delete_obs, "Delete observations", orgid, "delete", "observations", TRUE);
    -- delete forecast
    SET delete_fx = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        delete_fx, "Delete forecasts", orgid, "delete", "forecasts", TRUE);
    -- delete cdf forecasts
    SET delete_cdf = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        delete_cdf, "Delete probabilistic forecasts", orgid, "delete", "cdf_forecasts", TRUE);
    -- delete aggregates
    SET delete_aggregates = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        delete_aggregates, "Delete aggregates", orgid, "delete", "aggregates", TRUE);
    -- delete reports
    SET delete_reports = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        delete_reports, "Delete reports", orgid, "delete", "reports", TRUE);
    SET delete_sites = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        delete_sites, "Delete sites", orgid, "delete", "sites", TRUE);
    -- add all write perms to the role
    INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (
        roleid, delete_obs), (
        roleid, delete_fx), (
        roleid, delete_cdf), (
        roleid, delete_aggregates), (
        roleid, delete_reports), (
        roleid, delete_sites);
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_delete_role TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_delete_role TO 'frameworkadmin'@'%';


CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_default_admin_role(
    IN orgid BINARY(16))
COMMENT "Creates an organization administrator role with permissions on rbac objects"
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    -- parse orgid
    DECLARE roleid BINARY(16);
    DECLARE create_roles BINARY(16);
    DECLARE create_perms BINARY(16);
    DECLARE grant_roles BINARY(16);
    DECLARE revoke_roles BINARY(16);
    DECLARE update_roles BINARY(16);
    DECLARE update_permissions BINARY(16);
    DECLARE delete_roles BINARY(16);
    DECLARE delete_permissions BINARY(16);
    DECLARE read_users BINARY(16);
    DECLARE read_roles BINARY(16);
    DECLARE read_permissions BINARY(16);
    -- Administer data access control
    SET roleid = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.roles(
        name, description, id, organization_id) VALUES(
        'Administer data access controls', 'Administer users roles and permissions', roleid , orgid);
    -- create roles
    SET create_roles = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        create_roles, "Create roles", orgid, "create", "roles", TRUE);
    -- create permissions
    SET create_perms = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        create_perms, "Create permissions", orgid, "create", "permissions", TRUE);
    -- grant roles 
    SET grant_roles = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        grant_roles, "Grant roles", orgid, "grant", "roles", TRUE);
    -- revoke roles
    SET revoke_roles = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        revoke_roles, "Revoke roles", orgid, "revoke", "roles", TRUE);
    -- update roles
    SET update_roles = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        update_roles, "Update roles", orgid, "update", "roles", TRUE);
    -- update permissions
    SET update_permissions = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        update_permissions, "Update permissions", orgid, "update", "permissions", TRUE);
    -- delete roles
    SET delete_roles = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        delete_roles, "Delete roles", orgid, "delete", "roles", TRUE);
    -- delete permissions
    SET delete_permissions = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        delete_permissions, "Delete permissions", orgid, "delete", "permissions", TRUE);
    -- read users
    SET read_users = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_users, "Read users", orgid, "read", "users", TRUE);
    -- read roles
    SET read_roles = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_roles, "Read roles", orgid, "read", "roles", TRUE);
    -- read permissions
    SET read_permissions = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_permissions, "Read permissions", orgid, "read", "permissions", TRUE);
    INSERT INTO arbiter_data.role_permission_mapping(role_id, permission_id) VALUES (
        roleid, create_roles), (
        roleid, create_perms), (
        roleid, grant_roles), (
        roleid, revoke_roleS), (
        roleid, update_roles), (
        roleid, update_permissions), (
        roleid, delete_roles), (
        roleid, delete_permissions), (
        roleid, read_users), (
        roleid, read_roles), (
        roleid, read_permissions);
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_admin_role TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_admin_role TO 'frameworkadmin'@'%';


/*
 * Get a role id by name and organization
 */
CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_org_role_by_name(
    role_name VARCHAR(64), orgid BINARY(16))
RETURNS BINARY(16)
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    RETURN (SELECT id FROM arbiter_data.roles
        WHERE organization_id = orgid AND name = role_name LIMIT 1);
END;
GRANT EXECUTE ON FUNCTION arbiter_data.get_org_role_by_name TO 'select_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_org_role_by_name TO 'frameworkadmin'@'%';


/*
 * Promote user to organization admin
 */
CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE promote_user_to_org_admin (
    IN struserid CHAR(36), IN strorgid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    -- ensure user is in organization
    DECLARE orgid BINARY(16);
    DECLARE userid BINARY(16);
    SET orgid = UUID_TO_BIN(strorgid, 1);
    SET userid = UUID_TO_BIN(struserid, 1);
    IF orgid = get_object_organization(userid, 'users') THEN
        -- add all default roles to user
        INSERT INTO arbiter_data.user_role_mapping(user_id, role_id) VALUES(
            userid, get_org_role_by_name('Create metadata', orgid)), (
            userid, get_org_role_by_name('Read all', orgid)), (
            userid, get_org_role_by_name('Write all values', orgid)), (
            userid, get_org_role_by_name('Delete metadata', orgid)), (
            userid, get_org_role_by_name('Administer data access controls', orgid));
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = "Cannot promote admin from outside organization.",
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.promote_user_to_org_admin TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.promote_user_to_org_admin TO 'frameworkadmin'@'%';
GRANT EXECUTE ON FUNCTION arbiter_data.get_org_role_by_name TO 'insert_rbac'@'localhost';


/*
 * Add user to organization (orgid, userid)
 */
CREATE DEFINER = 'update_rbac'@'localhost' PROCEDURE add_user_to_org(
    IN struserid CHAR(36), IN strorgid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE userid BINARY(16);
    SET orgid = UUID_TO_BIN(strorgid, 1);
    SET userid = UUID_TO_BIN(struserid, 1);
    -- ensure the user belongs to Unaffiliated org
    IF get_organization_id('Unaffiliated') = get_object_organization(userid, 'users') THEN
        UPDATE arbiter_data.users SET organization_id = orgid WHERE id = userid;
    ELSE
        -- error user in organization
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Cannot add affiliated user to organization',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT SELECT(id), UPDATE ON arbiter_data.users TO 'update_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'update_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_user_to_org TO 'update_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_user_to_org TO 'frameworkadmin'@'%';


/*
 * Remove all roles from a user other than those in Unaffiliated and Reference
 */
CREATE DEFINER = 'delete_rbac'@'localhost' PROCEDURE remove_org_roles_from_user(
    IN userid BINARY(16))
COMMENT "Remove all roles from the user except the defaults"
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE unaffiliated_orgid BINARY(16);
    DECLARE reference_orgid BINARY(16);
    SET unaffiliated_orgid = get_organization_id('Unaffiliated');
    SET reference_orgid = get_organization_id('Reference');
    DELETE FROM arbiter_data.user_role_mapping
        WHERE user_id = userid AND role_id IN (
            SELECT id FROM arbiter_data.roles
            WHERE organization_id NOT IN (unaffiliated_orgid, reference_orgid));
END;
GRANT SELECT (organization_id) ON arbiter_data.roles TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_org_roles_from_user TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_org_roles_from_user TO 'update_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_organization_id TO 'delete_rbac'@'localhost';


/*
 * Remove non-unafiliated roles and update user's org to unaffiliated.
 */
CREATE DEFINER = 'update_rbac'@'localhost' PROCEDURE move_user_to_unaffiliated(
    IN struserid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE userid BINARY(16);
    SET userid = UUID_TO_BIN(struserid, 1);
    -- remove all Organizational roles from the user
    CALL remove_org_roles_from_user(userid);
    -- update user's organization to Unaffiliated
    UPDATE arbiter_data.users SET organization_id = get_organization_id('Unaffiliated') WHERE id = userid;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.move_user_to_unaffiliated TO 'update_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.move_user_to_unaffiliated TO 'frameworkadmin'@'%';
GRANT EXECUTE ON FUNCTION arbiter_data.get_organization_id TO 'update_rbac'@'localhost';


/*
 * delete user
 * perhaps using this is better than removing a user from an org
 */ 
CREATE DEFINER = 'delete_rbac'@'localhost' PROCEDURE delete_user(
    IN struserid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE userid BINARY(16);
    SET userid = UUID_TO_BIN(struserid, 1);
    IF EXISTS(SELECT 1 FROM arbiter_data.users WHERE id = userid) THEN
        DELETE FROM arbiter_data.users WHERE id = userid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not exist',
        MYSQL_ERRNO = 1305;
    END IF;
END;
GRANT SELECT (id), DELETE ON arbiter_data.users TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_user TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_user TO 'frameworkadmin'@'%';


/*
 * List all users in the framework
 */
CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE list_all_users()
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    SELECT auth0_id, BIN_TO_UUID(id, 1) as id,
        get_organization_name(organization_id) as organization_name,
        BIN_TO_UUID(organization_id, 1) as organization_id
        FROM arbiter_data.users;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.list_all_users TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_all_users TO 'frameworkadmin'@'%';


/*
 * List all organizations in the framework
 */
CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE list_all_organizations()
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    SELECT name, BIN_TO_UUID(id, 1) as id, accepted_tou from arbiter_data.organizations;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.list_all_organizations TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_all_organizations TO 'frameworkadmin'@'%';


/*
 * Updates an organization to have accepted terms of use
 */
CREATE DEFINER = 'update_rbac'@'localhost' PROCEDURE set_org_accepted_tou(
    IN strorgid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    SET orgid = UUID_TO_BIN(strorgid, 1);
    IF EXISTS(SELECT 1 FROM arbiter_data.organizations WHERE id = orgid) THEN
        UPDATE arbiter_data.organizations SET accepted_tou = TRUE WHERE id = orgid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Organization does not exist',
        MYSQL_ERRNO = 1305;
    END IF;
END;
GRANT SELECT (id), UPDATE ON arbiter_data.organizations TO 'update_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.set_org_accepted_tou TO 'update_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.set_org_accepted_tou TO 'frameworkadmin'@'%';
