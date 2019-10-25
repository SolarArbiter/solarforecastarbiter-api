ALTER TABLE arbiter_data.forecasts DROP FOREIGN KEY forecasts_sites_fk,
    DROP FOREIGN KEY forecasts_aggregates_fk,
    ADD FOREIGN KEY forecasts_ibfk_2 (site_id) REFERENCES sites(id) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE arbiter_data.forecasts MODIFY COLUMN site_id BINARY(16) NOT NULL, DROP COLUMN aggregate_id;


DROP TRIGGER limit_forecasts_update;
-- restrict fields that can be updated in forecasts
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER limit_forecasts_update BEFORE UPDATE ON arbiter_data.forecasts
FOR EACH ROW
BEGIN
    IF NEW.organization_id != OLD.organization_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify orgnization_id of forecast object';
    ELSEIF NEW.site_id != OLD.site_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify site_id of forecast object';
    END IF;
END;

CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER fail_on_aggregate_delete_if_forecast BEFORE DELETE ON arbiter_data.aggregates
FOR EACH ROW
BEGIN
    DECLARE fxexists BOOLEAN;
    SET fxexists = (
        SELECT 1 FROM forecasts WHERE site_id = OLD.id LIMIT 1
    );
    IF fxexists IS NOT NULL AND fxexists THEN
        SIGNAL SQLSTATE '23000' SET MESSAGE_TEXT = 'Aggregate cannot be deleted, a forecast still references it.', MYSQL_ERRNO = 1451;
    END IF;
END;


DROP PROCEDURE list_forecasts;
-- Create procedure to return list of forecasts a user can read
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_forecasts (IN auth0id VARCHAR(32))
COMMENT 'List all forecasts and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as forecast_id, get_organization_name(organization_id) as provider,
    BIN_TO_UUID(site_id, 1) as site_id, name, variable, issue_time_of_day, lead_time_to_start,
    interval_label, interval_length, run_length, interval_value_type, extra_parameters,
    created_at, modified_at
FROM forecasts WHERE id in (
     SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'forecasts');

GRANT EXECUTE ON PROCEDURE list_forecasts TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE list_forecasts TO 'apiuser'@'%';


DROP PROCEDURE store_forecast;
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_forecast (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN site_id CHAR(36), IN name VARCHAR(64), IN variable VARCHAR(32),
  IN issue_time_of_day VARCHAR(5), IN lead_time_to_start SMALLINT UNSIGNED, IN interval_label VARCHAR(32),
  IN interval_length SMALLINT UNSIGNED, IN run_length SMALLINT UNSIGNED, IN interval_value_type VARCHAR(32),
  IN extra_parameters TEXT)
COMMENT 'Store an forecast object. User must be able to read site information.'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE binsiteid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE canreadsite BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'forecasts'));
    SET binsiteid = (SELECT UUID_TO_BIN(site_id, 1));
    IF allowed THEN
       SET canreadsite = (SELECT can_user_perform_action(auth0id, binsiteid, 'read'));
       IF canreadsite THEN
           SELECT get_user_organization(auth0id) INTO orgid;
           INSERT INTO arbiter_data.forecasts (
               id, organization_id, site_id, name, variable, issue_time_of_day, lead_time_to_start,
               interval_label, interval_length, run_length, interval_value_type, extra_parameters
           ) VALUES (
               UUID_TO_BIN(strid, 1), orgid, binsiteid, name, variable, issue_time_of_day,
               lead_time_to_start, interval_label, interval_length, run_length, interval_value_type,
               extra_parameters);
       ELSE
           SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not have permission to read site', MYSQL_ERRNO = 1143;
       END IF;
    ELSE
       SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create forecasts"',
       MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE store_forecast TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE store_forecast TO 'apiuser'@'%';


DROP PROCEDURE read_forecast;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_forecast (
IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read forecast metadata'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as forecast_id, get_organization_name(organization_id) as provider,
            BIN_TO_UUID(site_id, 1) as site_id, name, variable, issue_time_of_day, lead_time_to_start,
            interval_label, interval_length, run_length, interval_value_type, extra_parameters,
            created_at, modified_at
        FROM arbiter_data.forecasts WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read forecast"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE read_forecast TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE read_forecast TO 'apiuser'@'%';


ALTER TABLE arbiter_data.cdf_forecasts_groups DROP FOREIGN KEY cdf_forecasts_sites_fk,
    DROP FOREIGN KEY cdf_forecasts_aggregates_fk,
    ADD FOREIGN KEY cdf_forecasts_groups_ibfk_2 (site_id) REFERENCES sites(id) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE arbiter_data.cdf_forecasts_groups MODIFY COLUMN site_id BINARY(16) NOT NULL, DROP COLUMN aggregate_id;
