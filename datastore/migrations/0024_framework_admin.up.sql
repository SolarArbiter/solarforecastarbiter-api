/*
 * Establish new mysql user
 */
-- @localhost?
CREATE USER 'frameworkadmin'@'%' IDENTIFIED BY 'thisisaterribleandpublicpassword';

/*
 * Create an organization
 * Should the default be accepted_tou = true? or 
 * false and manual update
 */
CREATE DEFINER = 'insert_rbac'@'localhost' create_organization (
    IN org_name VARCHAR(32))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    -- set orgid
    DECLARE orgid BINARY(16);
    SET orgid = (SELECT UUID_TO_BIN(UUID(), 1));
    -- insert into organization
    INSERT INTO arbiter_data.organizations(name, id accepted_tou) VALUES (
        org_name, orgid, TRUE);
END;


-- establish base roles
CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_default_read_role(
    IN strorgid BINARY(16))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    -- parse orgid
    DECLARE orgid BINARY(16);
    SET orgid = UUID_TO_BIN(strordig, 1);
    -- View all data/metadata
    DECLARE roleid BINARY(16);
    SET roleid = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.roles)
        name, description, id, organization_id) VALUES(
        'Read all', 'View all data and metadata', orgid);
    -- read all sites
    DECLARE read_sites BINARY(16);
    SET read_sites = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_sites, "Read all sites", orgid, "read", "sites", TRUE);
    -- read all observations
    DECLARE read_obs BNINARY(16);
    SET read_obs = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_obs, "Read all observations", orgid, "read", "observations", TRUE);
    -- read_vallues all observations
    DECLARE read_obs_values BINARY(16);
    SET read_obs_values = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_obs_values, "Read all observation values", orgid, "read_values", "observations", TRUE);
    -- read all forecasts
    DECLARE read_fx BINARY(16);
    SET read_fx = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_fx, "Read all forecasts", orgid, "read", "forecasts", TRUE);
    -- read_values all forecasts
    DECLARE read_fx_values BINARY(16);
    SET read_fx_values = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_fx_values, "Read all forecast values", orgid, "read_values", "forecasts", TRUE);
    -- read all cdf_forecast_groups
    DECLARE read_cdf BINARY(16);
    SET read_cdf = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_cdf, "Read all probabilistic forecasts", orgid, "read", "cdf_forecasts", TRUE);
    -- read_values all cdf_forecast_groups
    DECLARE read_cdf_values BINARY(16);
    SET read_cdf_values = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_cdf_values, "Read all probabilistic forecast values", orgid, "read_values", "cdf_forecasts", TRUE);
    -- read all reports
    DECLARE read_reports BINARY(16);
    SET read_reports = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_reports, "Read all reports", orgid, "read", "reports", TRUE);
    -- read_values all reports
    DECLARE read_report_values BINARY(16);
    SET read_report_values = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_report_values, "Read all report values", orgid, "read_vales", "reports", TRUE);
    -- read all aggregates
    DECLARE read_agg BINARY(16);
    SET read_agg = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        read_agg, "Read all aggregates", orgid, "read", "aggregates", TRUE);
    -- read_values all aggregates
    DECLARE read_agg_values BINARY(16);
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

CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_default_write_role(
    IN strorgid BINARY(16))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    -- parse orgid
    DECLARE orgid BINARY(16);
    SET orgid = UUID_TO_BIN(strordig, 1);
    -- Write all values
    DECLARE roleid BINARY(16);
    SET roleid = (SELECT UUID_TO_BIN(UUID(), 1));
    INSERT INTO arbiter_data.roles(
        name, description, id, organization_id) VALUES(
        'Write all values', 'Allows the user to submit data within the organization', orgid);
    -- write_values all observations
    DECLARE write_obs BINARY(16);
    SET write_obs = UUID_TO_BIN(UUID(), 1);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
        write_obs, "Submit values to all observations", orgid, "write_values", "observations", TRUE);
    
    -- write_values all forecasts
    -- write_values all cdf_forecast_groups
    -- write_values all aggregates?
END;


CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_default_create_role(
    IN orgid BINARY(16))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
  -- Create Metadata
    -- create observations
    -- create forecasts
    -- create cdf_forecast_groups
    -- create reports
    -- create aggregates
END;

CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_default_admin_role(
    IN orgid BINARY(16))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
  -- Administer data access control
    -- create roles
    -- create permissions
    -- grant roles 
    -- revoke roles
    -- update roles
    -- update permissions
END;

/*
 * Promote user to organization admin (orgid, userid)
 */
CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE promote_user_to_org_admin (
    IN userid BINARY(16), IN orgid BINARY(16))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN

    -- ensure user is in organization
    -- add all default roles to user
END;

/*
 * Add user to organization (orgid, userid)
 */
CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE add_user_to_org(
    IN userid BINARY(16), IN orgid BINARY(16))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
-- ensure the user belongs to Unaffiliated org
-- update the user's organization
END;


/*
 * Remove user from organization
 */
-- remove all non-unaffiliated Organizational roles from the user
-- update user's organization to Unaffiliated


/*
 * delete user
 */ 
-- delete the user

/*
 * Access to other procedures? this would require some finagling of the rbac system
 */
