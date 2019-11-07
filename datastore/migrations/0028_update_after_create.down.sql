DROP FUNCTION get_default_user_role;
DROP PROCEDURE add_object_permission_to_default_user_role;

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
    DECLARE binsiteid BINARY(16) DEFAULT NULL;
    DECLARE binaggid BINARY(16) DEFAULT NULL;
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE canreadsite BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'cdf_forecasts'));
    SET binsiteaggid = (SELECT UUID_TO_BIN(site_or_agg_id, 1));
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
               UUID_TO_BIN(strid, 1), orgid, binsiteid, binaggid, name, variable, issue_time_of_day,
               lead_time_to_start, interval_label, interval_length, run_length, interval_value_type,
               extra_parameters, axis);
       ELSE
           SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not have permission to read site/aggregate', MYSQL_ERRNO = 1143;
       END IF;
    ELSE
       SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create cdf forecasts"',
       MYSQL_ERRNO = 1142;
    END IF;
END;
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
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'reports'));
    IF allowed THEN
        SELECT get_user_organization(auth0id) INTO orgid;
        INSERT INTO arbiter_data.reports (
            id, organization_id, name, report_parameters
        ) VALUES (
            UUID_TO_BIN(strid, 1), orgid, name, report_parameters);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create reports"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE store_report TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE store_report TO 'apiuser'@'%';
