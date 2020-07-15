CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_trial_user(IN auth0id VARCHAR(32), IN orgid CHAR(36), IN add_reference_role BOOLEAN)
COMMENT 'Inserts a new trial user into the organization and add permission to read reference data only, returning new user id'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE userid BINARY(16);
    DECLARE binorgid BINARY(16);
    SET userid = UUID_TO_BIN(UUID(), 1);
    SET binorgid = UUID_TO_BIN(orgid, 1);
    INSERT INTO arbiter_data.users (id, auth0_id, organization_id) VALUES (
        userid, auth0id, binorgid);
    IF add_reference_role THEN
        CALL arbiter_data.add_reference_role_to_user(userid);
    END IF;
    CALL arbiter_data.create_default_user_role(userid, binorgid);
    SELECT BIN_TO_UUID(userid, 1);
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.create_trial_user TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_trial_user TO 'frameworkadmin'@'%';


CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_trial_role_on_reference_data (IN objects JSON, IN trial_name VARCHAR(64), OUT roleid BINARY(16))
COMMENT 'Create a role that provides the read access to select reference data'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE reforg BINARY(16);
    DECLARE roleperm BINARY(16);
    DECLARE permission_table JSON;
    DECLARE invalidobjects BOOLEAN;

    SET roleid = UUID_TO_BIN(UUID(), 1);
    SET roleperm = UUID_TO_BIN(UUID(), 1);
    SET reforg = get_organization_id('Reference');

    -- first check that all objects are valid
    SET invalidobjects = (SELECT NOT IFNULL(COUNT(*), FALSE) FROM JSON_TABLE(objects, '$[*]' COLUMNS(
        id CHAR(36) PATH '$.id' ERROR ON EMPTY ERROR ON ERROR,
        object_type VARCHAR(32) PATH '$.object_type' ERROR ON EMPTY ERROR ON ERROR)
    ) AS ot WHERE get_object_organization(UUID_TO_BIN(ot.id, 1), ot.object_type) = reforg);

    IF invalidobjects THEN
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Items in objects do not belong to Reference organization',
        MYSQL_ERRNO = 1216;
    END IF;

    SET permission_table = JSON_ARRAY(
        JSON_OBJECT('id', UUID(), 'description', 'Read reports for ', 'action', 'read', 'object_type', 'reports'),
        JSON_OBJECT('id', UUID(), 'description', 'Read report values for ', 'action', 'read_values', 'object_type', 'reports'),
        JSON_OBJECT('id', UUID(), 'description', 'Read sites for ', 'action', 'read', 'object_type', 'sites'),
        JSON_OBJECT('id', UUID(), 'description', 'Read forecasts for ', 'action', 'read', 'object_type', 'forecasts'),
        JSON_OBJECT('id', UUID(), 'description', 'Read forecast values for ', 'action', 'read_values', 'object_type', 'forecasts'),
        JSON_OBJECT('id', UUID(), 'description', 'Read observations for ', 'action', 'read', 'object_type', 'observations'),
        JSON_OBJECT('id', UUID(), 'description', 'Read observation values for ', 'action', 'read_values', 'object_type', 'observations'),
        JSON_OBJECT('id', UUID(), 'description', 'Read cdf_forecasts for ', 'action', 'read', 'object_type', 'cdf_forecasts'),
        JSON_OBJECT('id', UUID(), 'description', 'Read cdf_forecast values for ', 'action', 'read_values', 'object_type', 'cdf_forecasts'),
        JSON_OBJECT('id', UUID(), 'description', 'Read aggregates for ', 'action', 'read', 'object_type', 'aggregates'),
        JSON_OBJECT('id', UUID(), 'description', 'Read aggregate values for ', 'action', 'read_values', 'object_type', 'aggregates')
    );

    INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES (
        CONCAT(trial_name, ' Support'), CONCAT('Allow reading of select reference data for ', trial_name),
        roleid, reforg);
    INSERT INTO arbiter_data.permissions (id, description, organization_id, applies_to_all, action, object_type)
        SELECT UUID_TO_BIN(pt.id, 1), CONCAT(pt.description, trial_name), reforg, FALSE, pt.action,
        pt.object_type FROM JSON_TABLE(
            permission_table, "$[*]" COLUMNS (
                id CHAR(36) PATH '$.id',
                description VARCHAR(64) PATH '$.description',
                action VARCHAR(32) PATH '$.action',
                object_type VARCHAR(32) PATH '$.object_type')
        ) AS pt;
    INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id)
        SELECT roleid, UUID_TO_BIN(pt.id, 1) FROM JSON_TABLE(
            permission_table, "$[*]" COLUMNS (
                id CHAR(36) PATH '$.id')) AS pt;

    -- add permission to read the role
    INSERT INTO arbiter_data.permissions (id, description, organization_id, applies_to_all, action, object_type)
    VALUES (roleperm, CONCAT('Read the reference role for ', trial_name, ' support'), reforg, FALSE, 'read', 'roles');
    INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (roleid, roleperm);
    INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) VALUES (roleperm, roleid);
    -- choose not to give read permission to the permission objects

    INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
        SELECT UUID_TO_BIN(pt.id, 1), UUID_TO_BIN(ot.id, 1) FROM JSON_TABLE(permission_table, '$[*]' COLUMNS (
            id CHAR(36) PATH '$.id', object_type VARCHAR(32) PATH '$.object_type')
        ) AS pt JOIN JSON_TABLE(objects, '$[*]' COLUMNS(
            id CHAR(36) PATH '$.id' ERROR ON EMPTY ERROR ON ERROR,
            object_type VARCHAR(32) PATH '$.object_type' ERROR ON EMPTY ERROR ON ERROR)
        ) AS ot ON pt.object_type = ot.object_type WHERE get_object_organization(UUID_TO_BIN(ot.id, 1),
            ot.object_type) = reforg;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.create_trial_role_on_reference_data TO 'insert_rbac'@'localhost';


-- add new role to trial users
CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE add_reference_permissions_for_trial_users(IN users JSON, IN objects JSON, IN trial_name VARCHAR(64))
COMMENT 'Creates a role that provides the read access to select reference data and adds the role for each user'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE roleid BINARY(16);
    CALL create_trial_role_on_reference_data(objects, trial_name, roleid);
    INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) SELECT UUID_TO_BIN(userid, 1), roleid FROM JSON_TABLE(
        users, '$[*]' COLUMNS(userid CHAR(36) PATH '$' ERROR ON EMPTY ERROR ON ERROR)) AS jt;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.add_reference_permissions_for_trial_users TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_reference_permissions_for_trial_users TO 'frameworkadmin'@'%';
