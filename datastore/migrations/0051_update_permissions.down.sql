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
            userid, get_org_role_by_name('Delete metadata', orgid)), (
            userid, get_org_role_by_name('Administer data access controls', orgid));
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = "Cannot promote admin from outside organization.",
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.promote_user_to_org_admin TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.promote_user_to_org_admin TO 'frameworkadmin'@'%';


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
    CALL create_default_admin_role(orgid);
END;
GRANT INSERT ON arbiter_data.organizations TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_organization TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_organization TO 'frameworkadmin'@'%';


DROP PROCEDURE create_default_update_role;

DELETE FROM arbiter_data.permissions WHERE action = 'update' AND applies_to_all AND description in (
    'Update all sites', 'Update all observations', 'Update all forecasts', 'Update all probabilistic forecasts',
    'Update all aggregates') AND id in (
        SELECT permission_id from arbiter_data.role_permission_mapping WHERE role_id IN (
            SELECT id FROM arbiter_data.roles WHERE name = 'Update all' AND description = 'Update all metadata'
        ));
DELETE FROM arbiter_data.roles WHERE name = 'Update all' AND description = 'Update all metadata';
