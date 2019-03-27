-- create user for procedures and don't allow this user to log in to the server
CREATE USER 'select_rbac'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;


-- Procedure to list all the objects a user can read
CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE list_objects_user_can_read (IN auth0id VARCHAR(32), IN objtype VARCHAR(32))
COMMENT 'List the objects a user can read'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE uid BINARY(16);
    SELECT id INTO uid FROM users WHERE auth0_id = auth0id;
    SELECT object_id FROM permission_object_mapping WHERE permission_id IN (
        SELECT permission_id FROM role_permission_mapping WHERE role_id IN (
           SELECT role_id FROM user_role_mapping WHERE user_id = uid
         )
    ) AND permission_id IN (
        SELECT id FROM permissions WHERE action = 'read' AND object_type = objtype
    );
END;


-- Function to check if the user can perform the requested action
CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION can_user_perform_action (auth0id VARCHAR(32), objectid BINARY(16), theaction VARCHAR(32))
RETURNS BOOLEAN
COMMENT 'Can the user perform the action on the object?'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE isin BOOL DEFAULT 0;
    DECLARE uid BINARY(16);
    SELECT id INTO uid FROM users WHERE auth0_id = auth0id;
    SET isin = (
        SELECT 1 FROM permission_object_mapping WHERE permission_id IN (
            SELECT permission_id FROM role_permission_mapping WHERE role_id IN (
                SELECT role_id FROM user_role_mapping WHERE user_id = uid
            )
        ) AND permission_id IN (
            SELECT id FROM permissions WHERE action = theaction
        ) AND object_id = objectid LIMIT 1
    );
    IF isin IS NOT NULL AND isin THEN
       RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;


-- Function to check if the user can create an object of the requested type
CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION user_can_create (auth0id VARCHAR(32), objecttype VARCHAR(32))
RETURNS BOOLEAN
COMMENT 'Can the user create objects of the type requested? Limited to user organization'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE uid BINARY(16);
    DECLARE oid BINARY(16);
    DECLARE isin BOOLEAN;
    SELECT id, organization_id INTO uid, oid FROM users WHERE auth0_id = auth0id;
    SET isin =  (
        SELECT 1 FROM permissions WHERE id IN (
            SELECT permission_id FROM role_permission_mapping WHERE role_id IN (
                SELECT role_id FROM user_role_mapping WHERE user_id = uid
            )
        ) AND action = 'create' AND object_type = objecttype
          AND organization_id = oid LIMIT 1
    );
    IF isin IS NOT NULL AND isin THEN
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;


-- Function to get organization_id of user
CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_user_organization (auth0id VARCHAR(32))
RETURNS BINARY(16)
COMMENT 'Returns the organizaton ID of the user'
READS SQL DATA SQL SECURITY DEFINER
RETURN (SELECT organization_id FROM arbiter_data.users WHERE auth0_id = auth0id);


-- function to get organization name
CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_organization_name (orgid BINARY(16))
RETURNS VARCHAR(32)
COMMENT 'Return the name of the organization'
READS SQL DATA SQL SECURITY DEFINER
RETURN (SELECT name from arbiter_data.organizations WHERE id = orgid);


-- Grant only required permissions to limited user account to execute rbac functions
GRANT SELECT ON `arbiter_data`.`permission_object_mapping` TO `select_rbac`@`localhost`;
GRANT SELECT ON `arbiter_data`.`permissions` TO `select_rbac`@`localhost`;
GRANT SELECT ON `arbiter_data`.`roles` TO `select_rbac`@`localhost`;
GRANT SELECT ON `arbiter_data`.`role_permission_mapping` TO `select_rbac`@`localhost`;
GRANT SELECT ON `arbiter_data`.`user_role_mapping` TO `select_rbac`@`localhost`;
GRANT SELECT ON `arbiter_data`.`users` TO `select_rbac`@`localhost`;
GRANT SELECT ON `arbiter_data`.`organizations` TO `select_rbac`@`localhost`;
GRANT EXECUTE ON PROCEDURE `arbiter_data`.`list_objects_user_can_read` TO `select_rbac`@`localhost`;
GRANT EXECUTE ON FUNCTION `arbiter_data`.`can_user_perform_action` TO `select_rbac`@`localhost`;
GRANT EXECUTE ON FUNCTION `arbiter_data`.`user_can_create` TO `select_rbac`@`localhost`;
GRANT EXECUTE ON FUNCTION `arbiter_data`.`get_user_organization` TO `select_rbac`@`localhost`;
GRANT EXECUTE ON FUNCTION `arbiter_data`.`get_organization_name` TO `select_rbac`@`localhost`;
