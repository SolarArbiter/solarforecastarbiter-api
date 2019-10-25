ALTER TABLE arbiter_data.forecasts MODIFY COLUMN site_id BINARY(16),
    ADD COLUMN aggregate_id BINARY(16) AFTER site_id;

ALTER TABLE arbiter_data.forecasts DROP FOREIGN KEY forecasts_ibfk_2,
    ADD FOREIGN KEY forecasts_sites_fk (site_id) REFERENCES sites(id) ON DELETE SET NULL ON UPDATE RESTRICT,
    ADD FOREIGN KEY forecasts_aggregates_fk (aggregate_id) REFERENCES aggregates(id) ON DELETE SET NULL ON UPDATE RESTRICT;


DROP TRIGGER limit_forecasts_update;
-- restrict fields that can be updated in forecasts
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER limit_forecasts_update BEFORE UPDATE ON arbiter_data.forecasts
FOR EACH ROW
BEGIN
    IF NEW.organization_id != OLD.organization_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify orgnization_id of forecast object';
    ELSEIF NEW.site_id != OLD.site_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify site_id of forecast object';
    ELSEIF NEW.aggregate_id != OLD.aggregate_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify aggregate_id of forecast object';
    END IF;
END;

DROP TRIGGER fail_on_aggregate_delete_if_forecast;


DROP PROCEDURE list_forecasts;
-- Create procedure to return list of forecasts a user can read
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_forecasts (IN auth0id VARCHAR(32))
COMMENT 'List all forecasts and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as forecast_id, get_organization_name(organization_id) as provider,
    BIN_TO_UUID(site_id, 1) as site_id, BIN_TO_UUID(aggregate_id, 1) as aggregate_id,
    name, variable, issue_time_of_day, lead_time_to_start,
    interval_label, interval_length, run_length, interval_value_type, extra_parameters,
    created_at, modified_at
FROM forecasts WHERE id in (
    SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'forecasts');

GRANT EXECUTE ON PROCEDURE list_forecasts TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE list_forecasts TO 'apiuser'@'%';


DROP PROCEDURE store_forecast;
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_forecast (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN site_or_agg_id CHAR(36), IN name VARCHAR(64), IN variable VARCHAR(32),
  IN issue_time_of_day VARCHAR(5), IN lead_time_to_start SMALLINT UNSIGNED, IN interval_label VARCHAR(32),
  IN interval_length SMALLINT UNSIGNED, IN run_length SMALLINT UNSIGNED, IN interval_value_type VARCHAR(32),
  IN extra_parameters TEXT, IN references_site BOOLEAN)
COMMENT 'Store an forecast object. User must be able to read site information.'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE binsiteaggid BINARY(16);
    DECLARE binsiteid BINARY(16) DEFAULT NULL;
    DECLARE binaggid BINARY(16) DEFAULT NULL;
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE canreadsite BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'forecasts'));
    SET binsiteaggid = (SELECT UUID_TO_BIN(site_or_aggid, 1));
    IF allowed THEN
       SET canreadsite = (SELECT can_user_perform_action(auth0id, binsiteaggid, 'read'));
       IF canreadsite THEN
           IF references_site THEN
               SET binsiteid = binsiteaggid;
           ELSE
               SET binaggid = binsiteaggid;
           END IF;
           SELECT get_user_organization(auth0id) INTO orgid;
           INSERT INTO arbiter_data.forecasts (
               id, organization_id, site_id, aggregate_id, name, variable, issue_time_of_day,
               lead_time_to_start, interval_label, interval_length, run_length, interval_value_type,
               extra_parameters
           ) VALUES (
               UUID_TO_BIN(strid, 1), orgid, binsiteid, binaggid, name, variable, issue_time_of_day,
               lead_time_to_start, interval_label, interval_length, run_length, interval_value_type,
               extra_parameters);
       ELSE
           SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not have permission to read site/aggregate', MYSQL_ERRNO = 1143;
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
            BIN_TO_UUID(site_id, 1) as site_id, BIN_TO_UUID(aggregate_id,1 ) as aggregate_id,
            name, variable, issue_time_of_day, lead_time_to_start,
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


SET @orgid = (SELECT UUID_TO_BIN('b76ab62e-4fe1-11e9-9e44-64006a511e6f', 1));
SET @aggid = UUID_TO_BIN('458ffc27-df0b-11e9-b622-62adb5fd6af0', 1);
INSERT INTO arbiter_data.forecasts (
    id, organization_id, aggregate_id, name, variable, issue_time_of_day, lead_time_to_start,
    interval_label, interval_length, run_length, interval_value_type, extra_parameters,
    created_at, modified_at
) VALUES (
    UUID_TO_BIN('39220780-76ae-4b11-bef1-7a75bdc784e3', 1),
    @orgid, @aggid,
    'GHI Aggregate FX', 'ghi', '06:00', 60, 'beginning', 60, 1440, 'interval_mean', '',
    TIMESTAMP('2019-03-01 11:55:37'), TIMESTAMP('2019-03-01 11:55:37')
);

INSERT INTO arbiter_data.forecasts_values (id, timestamp, value) SELECT UUID_TO_BIN('39220780-76ae-4b11-bef1-7a75bdc784e3', 1), timestamp, value FROM arbiter_data.forecasts_values where id = UUID_TO_BIN('11c20780-76ae-4b11-bef1-7a75bdc784e3', 1);


-- CDF Forecast modifications

ALTER TABLE arbiter_data.cdf_forecasts_groups MODIFY COLUMN site_id BINARY(16),
    ADD COLUMN aggregate_id BINARY(16) AFTER site_id;

ALTER TABLE arbiter_data.cdf_forecasts_groups DROP FOREIGN KEY cdf_forecasts_groups_ibfk_2,
    ADD FOREIGN KEY cdf_forecasts_sites_fk (site_id) REFERENCES sites(id) ON DELETE SET NULL ON UPDATE RESTRICT,
    ADD FOREIGN KEY cdf_forecasts_aggregates_fk (aggregate_id) REFERENCES aggregates(id) ON DELETE SET NULL ON UPDATE RESTRICT;



DROP PROCEDURE list_cdf_forecasts_groups;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_cdf_forecasts_groups (IN auth0id VARCHAR(32))
COMMENT 'List all cdf forecast groups and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as forecast_id,
       get_organization_name(organization_id) as provider,
       BIN_TO_UUID(site_id, 1) as site_id,
       BIN_TO_UUID(aggregate_id, 1) as aggregate_id,
       name, variable, issue_time_of_day, lead_time_to_start,
       interval_label, interval_length, run_length,
       interval_value_type, extra_parameters, axis,
       created_at, modified_at,
       get_constant_values(id) as constant_values
       FROM cdf_forecasts_groups WHERE id in (
           SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'cdf_forecasts');
GRANT EXECUTE ON PROCEDURE list_cdf_forecasts_groups TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE list_cdf_forecasts_groups TO 'apiuser'@'%';


DROP PROCEDURE list_cdf_forecasts_singles;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_cdf_forecasts_singles (IN auth0id VARCHAR(32))
COMMENT 'List all cdf forecast singletons and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(cfs.id, 1) as forecast_id, get_organization_name(cfg.organization_id) as provider,
       BIN_TO_UUID(cfg.site_id, 1) as site_id, BIN_TO_UUID(cfg.aggregate_id, 1) as aggregate_id,
       BIN_TO_UUID(cfs.cdf_forecast_group_id, 1) as parent,
       cfg.name as name, cfg.variable as variable,
       cfg.issue_time_of_day as issue_time_of_day, cfg.lead_time_to_start as lead_time_to_start,
       cfg.interval_label as interval_label, cfg.interval_length as interval_length,
       cfg.run_length as run_length, cfg.interval_value_type as interval_value_type,
       cfg.extra_parameters as extra_parameters, cfg.axis as axis, cfs.created_at as created_at,
       cfs.constant_value as constant_value
FROM cdf_forecasts_groups as cfg, cdf_forecasts_singles as cfs WHERE cfg.id in (
     SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'cdf_forecasts')
AND cfs.cdf_forecast_group_id = cfg.id;
GRANT EXECUTE ON PROCEDURE list_cdf_forecasts_singles TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE list_cdf_forecasts_singles TO 'apiuser'@'%';


DROP PROCEDURE read_cdf_forecasts_group;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_cdf_forecasts_group (
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read cdf forecast group metadata'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as forecast_id,
            get_organization_name(organization_id) as provider,
            BIN_TO_UUID(site_id, 1) as site_id,
            BIN_TO_UUID(aggregate_id, 1) as aggregate_id,
            name, variable,
            issue_time_of_day, lead_time_to_start,
            interval_label, interval_length,
            run_length, interval_value_type,
            extra_parameters, axis, created_at,
            modified_at,
            get_constant_values(id) as constant_values
        FROM cdf_forecasts_groups WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read cdf forecast group"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE read_cdf_forecasts_group TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE read_cdf_forecasts_group TO 'apiuser'@'%';


DROP PROCEDURE read_cdf_forecasts_single;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_cdf_forecasts_single (
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read cdf forecast singleton metadata'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE groupid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET groupid = (SELECT cdf_forecast_group_id FROM cdf_forecasts_singles WHERE id = binid);
    SET allowed = (SELECT can_user_perform_action(auth0id, groupid, 'read'));
    IF allowed THEN
        SELECT BIN_TO_UUID(cfs.id, 1) as forecast_id, get_organization_name(cfg.organization_id) as provider,
            BIN_TO_UUID(cfg.site_id, 1) as site_id, BIN_TO_UUID(cfg.aggregate_id, 1) as aggregate_id,
            BIN_TO_UUID(cfs.cdf_forecast_group_id, 1) as parent,
            cfg.name as name, cfg.variable as variable,
            cfg.issue_time_of_day as issue_time_of_day, cfg.lead_time_to_start as lead_time_to_start,
            cfg.interval_label as interval_label, cfg.interval_length as interval_length,
            cfg.run_length as run_length, cfg.interval_value_type as interval_value_type,
            cfg.extra_parameters as extra_parameters, cfg.axis as axis, cfs.created_at as created_at,
            cfs.constant_value as constant_value
        FROM cdf_forecasts_groups as cfg, cdf_forecasts_singles as cfs WHERE cfs.id = binid
        AND cfg.id = cfs.cdf_forecast_group_id;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read cdf forecast single"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE read_cdf_forecasts_single TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE read_cdf_forecasts_single TO 'apiuser'@'%';


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


DROP TRIGGER limit_cdf_forecasts_groups_update;
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER limit_cdf_forecasts_groups_update BEFORE UPDATE ON arbiter_data.cdf_forecasts_groups
FOR EACH ROW
BEGIN
    IF NEW.organization_id != OLD.organization_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify orgnization_id of cdf forecast object';
    ELSEIF NEW.site_id != OLD.site_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify site_id of cdf forecast object';
    ELSEIF NEW.aggregate_id != OLD.aggregate_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify aggregate_id of cdf forecast object';
    END IF;
END;


SET @cfg2 = UUID_TO_BIN('f6b620ca-f743-11e9-a34f-f4939feddd82', 1);
SET @cfg2time = TIMESTAMP('2019-03-02 14:55:38');
INSERT INTO arbiter_data.cdf_forecasts_groups (
    id, organization_id, aggregate_id, name, variable, issue_time_of_day, lead_time_to_start,
    interval_label, interval_length, run_length, interval_value_type, extra_parameters,
    created_at, modified_at, axis
) VALUES (
    @cfg2, @orgid, @aggid,
    'GHI Aggregate CDF FX', 'ghi', '06:00', 60, 'beginning', 60, 1440, 'interval_mean', '',
    @cfg2time, @cfg2time, 'y'
);

INSERT INTO arbiter_data.cdf_forecasts_singles (id, cdf_forecast_group_id, constant_value, created_at)
VALUES (
    UUID_TO_BIN('733f9396-50bb-11e9-8647-d663bd873d93', 1), @cfg2, 10.0, @cfg2time), (
    UUID_TO_BIN('733f9864-50bb-11e9-8647-d663bd873d93', 1), @cfg2, 20.0, @cfg2time), (
    UUID_TO_BIN('733f9b2a-50bb-11e9-8647-d663bd873d93', 1), @cfg2, 50.0, @cfg2time), (
    UUID_TO_BIN('733f9d96-50bb-11e9-8647-d663bd873d93', 1), @cfg2, 80.0, @cfg2time), (
    UUID_TO_BIN('733fa548-50bb-11e9-8647-d663bd873d93', 1), @cfg2, 100.0, @cfg2time);

INSERT INTO arbiter_data.cdf_forecasts_values (id, timestamp, value) SELECT t1.id, t2.timestamp, t2.value FROM cdf_forecasts_singles as t1, cdf_forecasts_values as t2 WHERE t2.id = UUID_TO_BIN('633f9396-50bb-11e9-8647-d663bd873d93', 1) AND t1.cdf_forecast_group_id = @cfg2;
