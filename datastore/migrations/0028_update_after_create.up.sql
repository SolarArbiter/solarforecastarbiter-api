CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_default_user_role(auth0id VARCHAR(32))
RETURNS BINARY(16)
COMMENT 'Get the ID of the default role of the user'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binuserid BINARY(16);
    DECLARE possiblerole BINARY(16);
    SET binuserid = (SELECT id FROM arbiter_data.users WHERE auth0_id = auth0id);
    SET possiblerole = (
        SELECT id from arbiter_data.roles WHERE name =
            CONCAT('DEFAULT User role ', BIN_TO_UUID(binuserid, 1))
        AND id IN (
            SELECT role_id FROM arbiter_data.user_role_mapping WHERE
            user_id = binuserid)
        );
    RETURN possiblerole;
END;

GRANT EXECUTE ON FUNCTION get_default_user_role TO 'select_rbac'@'localhost';


CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE add_object_permission_to_default_user_role(
    IN auth0id VARCHAR(32), IN objectorg BINARY(16), IN objectid BINARY(16), IN objecttype VARCHAR(32),
    IN action VARCHAR(32))
COMMENT 'Add permission to perform action on an object to the default user role'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
/* CAUTION this is only valid because the object, default user role, and
permission are all in the same org. Otherwise, it may be impossible for the
organization of that owns the object to remove the permission
from the user */
    DECLARE userrole BINARY(16);
    DECLARE userorg BINARY(16);
    DECLARE permid BINARY(16) DEFAULT UUID_TO_BIN(UUID(), 1);
    SET userrole = get_default_user_role(auth0id);
    SET userorg = get_user_organization(auth0id);
    IF objectorg = userorg AND NOT ISNULL(userrole) AND action != 'create' THEN
        INSERT INTO arbiter_data.permissions(
            id, description, organization_id, action, object_type, applies_to_all)
        VALUES (
            permid, CONCAT('Perform ', action, ' on ', BIN_TO_UUID(objectid, 1)),
            objectorg, action, objecttype, FALSE);
        INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) VALUES (
            permid, objectid);
        INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (
            userrole, permid);
    END IF;
END;

GRANT EXECUTE ON PROCEDURE add_object_permission_to_default_user_role TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION get_default_user_role TO 'insert_rbac'@'localhost';



DROP PROCEDURE store_cdf_forecasts_group;
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_cdf_forecasts_group (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN site_or_agg_id CHAR(36), IN name VARCHAR(64), IN variable VARCHAR(32),
  IN issue_time_of_day VARCHAR(5), IN lead_time_to_start SMALLINT UNSIGNED, IN interval_label VARCHAR(32),
  IN interval_length SMALLINT UNSIGNED, IN run_length SMALLINT UNSIGNED, IN interval_value_type VARCHAR(32),
  IN extra_parameters TEXT, IN axis VARCHAR(1), IN references_site BOOLEAN)
COMMENT 'Store an cdf forecast group object. User must be able to read site information.'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE binsiteaggid BINARY(16);
    DECLARE binid BINARY(16);
    DECLARE binsiteid BINARY(16) DEFAULT NULL;
    DECLARE binaggid BINARY(16) DEFAULT NULL;
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE canreadsite BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'cdf_forecasts'));
    SET binsiteaggid = UUID_TO_BIN(site_or_agg_id, 1);
    SET binid = UUID_TO_BIN(strid, 1);
    IF allowed THEN
       SET canreadsite = (SELECT can_user_perform_action(auth0id, binsiteaggid, 'read'));
       IF canreadsite THEN
           SELECT get_user_organization(auth0id) INTO orgid;
           IF references_site THEN
               SET binsiteid = binsiteaggid;
           ELSE
               SET binaggid = binsiteaggid;
           END IF;
           INSERT INTO arbiter_data.cdf_forecasts_groups (
               id, organization_id, site_id, aggregate_id, name, variable, issue_time_of_day,
               lead_time_to_start, interval_label, interval_length, run_length, interval_value_type,
               extra_parameters, axis
           ) VALUES (
               binid, orgid, binsiteid, binaggid, name, variable, issue_time_of_day,
               lead_time_to_start, interval_label, interval_length, run_length, interval_value_type,
               extra_parameters, axis);
           CALL add_object_permission_to_default_user_role(auth0id, orgid, binid, 'cdf_forecasts', 'update');
       ELSE
           SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not have permission to read site/aggregate', MYSQL_ERRNO = 1143;
       END IF;
    ELSE
       SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create cdf forecasts"',
       MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE add_object_permission_to_default_user_role TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE store_cdf_forecasts_group TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE store_cdf_forecasts_group TO 'apiuser'@'%';


DROP PROCEDURE store_report;
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_report (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN name VARCHAR(64),
    IN report_parameters JSON)
MODIFIES SQL DATA SQL SECURITY DEFINER
COMMENT 'Store report metadata'
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET allowed = user_can_create(auth0id, 'reports');
    SET binid = UUID_TO_BIN(strid, 1);
    IF allowed THEN
        SELECT get_user_organization(auth0id) INTO orgid;
        INSERT INTO arbiter_data.reports (
            id, organization_id, name, report_parameters
        ) VALUES (
            binid, orgid, name, report_parameters);
        CALL add_object_permission_to_default_user_role(auth0id, orgid, binid, 'reports', 'update');
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create reports"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE store_report TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE store_report TO 'apiuser'@'%';
