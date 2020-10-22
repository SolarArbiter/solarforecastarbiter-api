CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_default_update_role(
    IN orgid BINARY(16))
COMMENT "Role to update all metadata within the organization"
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE roleid BINARY(16);
    DECLARE update_sites BINARY(16);
    DECLARE update_obs BINARY(16);
    DECLARE update_fx BINARY(16);
    DECLARE update_cdf BINARY(16);
    DECLARE update_agg BINARY(16);
    SET roleid = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.roles(
        name, description, id, organization_id) VALUES(
        'Update all', 'Update all metadata', roleid, orgid);
    -- update all sites
    SET update_sites = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        update_sites, "Update all sites", orgid, "update", "sites", TRUE);
    -- update all observations
    SET update_obs = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        update_obs, "Update all observations", orgid, "update", "observations", TRUE);
    -- update all forecasts
    SET update_fx = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        update_fx, "Update all forecasts", orgid, "update", "forecasts", TRUE);
    -- update all cdf_forecast_groups
    SET update_cdf = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        update_cdf, "Update all probabilistic forecasts", orgid, "update", "cdf_forecasts", TRUE);
    -- update all aggregates
    SET update_agg = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        update_agg, "Update all aggregates", orgid, "update", "aggregates", TRUE);
    -- add update permissions to the role
    INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (
        roleid, update_sites), (
        roleid, update_obs), (
        roleid, update_fx), (
        roleid, update_cdf), (
        roleid, update_agg);
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_update_role TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_default_update_role TO 'frameworkadmin'@'%';


DROP PROCEDURE create_organization;
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
    CALL create_default_update_role(orgid);
    CALL create_default_admin_role(orgid);
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.create_organization TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_organization TO 'frameworkadmin'@'%';


DROP PROCEDURE promote_user_to_org_admin;
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
            userid, get_org_role_by_name('Update all', orgid)), (
            userid, get_org_role_by_name('Delete metadata', orgid)), (
            userid, get_org_role_by_name('Administer data access controls', orgid));
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = "Cannot promote admin from outside organization.",
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.promote_user_to_org_admin TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.promote_user_to_org_admin TO 'frameworkadmin'@'%';



CREATE PROCEDURE add_update_permissions()
MODIFIES SQL DATA
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE orgid BINARY(16);

    DECLARE cur0 CURSOR FOR SELECT id FROM organizations WHERE id != get_organization_id('Organization 1')
    AND id != get_organization_id('Unaffiliated');

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur0;
    first_loop: LOOP
        FETCH cur0 INTO orgid;
        IF done THEN
            LEAVE first_loop;
        END IF;
        CALL arbiter_data.create_default_update_role(orgid);
    END LOOP;
    CLOSE cur0;

    INSERT INTO arbiter_data.user_role_mapping (user_id, role_id)
    SELECT id, get_org_role_by_name('Update all', organization_id) FROM users WHERE
    id IN (SELECT user_id FROM user_role_mapping WHERE role_id = get_org_role_by_name('Create metadata', organization_id))
    AND id IN (SELECT user_id FROM user_role_mapping WHERE role_id = get_org_role_by_name('Read all', organization_id))
    AND id IN (SELECT user_id FROM user_role_mapping WHERE role_id = get_org_role_by_name('Write all values', organization_id))
    AND id IN (SELECT user_id FROM user_role_mapping WHERE role_id = get_org_role_by_name('Delete metadata', organization_id))
    AND id IN (SELECT user_id FROM user_role_mapping WHERE role_id = get_org_role_by_name('Administer data access controls', organization_id))
    AND organization_id != get_organization_id('Unaffiliated');
END;

-- Call and remove the procedure for updating existing users
CALL add_update_permissions();
DROP PROCEDURE add_update_permissions;
