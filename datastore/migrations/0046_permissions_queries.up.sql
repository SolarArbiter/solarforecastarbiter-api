CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE get_user_creatable_types(
    IN auth0id VARCHAR(32))
COMMENT 'Get a list of object types the user can create'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE userid BINARY(16);
    SET userid = (SELECT id FROM users WHERE auth0_id = auth0id);

    SELECT DISTINCT(perm.object_type) from permissions as perm
    WHERE action = 'create' AND perm.id IN(
        SELECT permission_id FROM role_permission_mapping
        WHERE role_id IN(
            SELECT role_id FROM user_role_mapping
            WHERE user_id = userid)
        );
END;

GRANT EXECUTE ON PROCEDURE get_user_creatable_types TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE get_user_creatable_types TO 'apiuser'@'%';


CREATE DEFINER = 'select_rbac'@'localhost' PROCEDURE list_actions_on_all_objects_of_type(
    IN auth0id VARCHAR(32), IN objecttype VARCHAR(32))
COMMENT 'List the uuids and actions users can take on all objects of a given type'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE userid BINARY(16);
    SET userid = (SELECT id FROM users WHERE auth0_id = auth0id);

	SELECT dt.id, json_arrayagg(dt.action) AS actions FROM (
		SELECT DISTINCT bin_to_uuid(object_id, 1) as id, action
		FROM permission_object_mapping
        INNER JOIN permissions ON (permission_object_mapping.permission_id=permissions.id)
		WHERE object_type=objecttype AND permission_id IN(
			SELECT permission_id
			FROM role_permission_mapping
			WHERE role_id in (
				SELECT role_id
				FROM user_role_mapping
				WHERE user_id = userid
			)
		)
	) as dt group by id;
END;

GRANT EXECUTE ON PROCEDURE list_actions_on_all_objects_of_type TO 'select_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE list_actions_on_all_objects_of_type TO 'apiuser'@'%';

