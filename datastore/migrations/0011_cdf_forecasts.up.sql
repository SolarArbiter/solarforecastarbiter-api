/* CDF Forecasts are sufficiently different from other forecasts that they
   get their own tables/procedures. We also want to keep things like  list_forecasts
   simple, so we don't add cdf things to the forecasts table.

   The CDF groups are the logical units.
   Permissions will be granted to the group objects and apply to all singles,
   so 'write' on the group allows write on each single.
*/

-- create cdf_forecast_group table
CREATE TABLE arbiter_data.cdf_forecasts_groups LIKE arbiter_data.forecasts;
ALTER TABLE arbiter_data.cdf_forecasts_groups ADD COLUMN (axis ENUM('x', 'y') NOT NULL);
ALTER TABLE arbiter_data.cdf_forecasts_groups ADD FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE arbiter_data.cdf_forecasts_groups ADD FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE RESTRICT ON UPDATE RESTRICT;


-- create the singles cdf forecast table
CREATE TABLE arbiter_data.cdf_forecasts_singles (
    id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
    cdf_forecast_group_id BINARY(16) NOT NULL,
    constant_value FLOAT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE (cdf_forecast_group_id, constant_value),
    FOREIGN KEY (cdf_forecast_group_id)
        REFERENCES arbiter_data.cdf_forecasts_groups(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


-- create the cdf forecasts values table
CREATE TABLE arbiter_data.cdf_forecasts_values (
    id BINARY(16) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    value FLOAT NOT NULL,

    PRIMARY KEY (id, timestamp),
    FOREIGN KEY (id)
    REFERENCES cdf_forecasts_singles(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


-- PERMISSIONS
ALTER TABLE arbiter_data.permissions CHANGE COLUMN object_type object_type ENUM('sites', 'aggregates', 'cdf_forecasts', 'forecasts', 'observations', 'users', 'roles', 'permissions') NOT NULL;


-- add permission triggers for cdf groups
GRANT SELECT, TRIGGER ON arbiter_data.cdf_forecasts_groups TO 'permission_trig'@'localhost';
GRANT TRIGGER ON arbiter_data.cdf_forecasts_singles TO 'permission_trig'@'localhost';

CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER add_object_perm_on_cdf_permissions_insert AFTER INSERT ON arbiter_data.permissions
FOR EACH ROW PRECEDES add_object_perm_on_permissions_insert
BEGIN
    IF NEW.applies_to_all AND NEW.action != 'create' THEN
        IF NEW.object_type = 'cdf_forecasts' THEN
            INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
                SELECT NEW.id, id FROM arbiter_data.cdf_forecasts_groups WHERE organization_id = NEW.organization_id;
        END IF;
    END IF;
END;


-- add trigger for inserts to cdf_forecasts_groups table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER add_object_perm_on_cdf_forecasts_groups_insert AFTER INSERT ON arbiter_data.cdf_forecasts_groups
FOR EACH ROW INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
    SELECT id, NEW.id FROM arbiter_data.permissions WHERE action != 'create' AND applies_to_all AND organization_id = NEW.organization_id AND object_type = 'cdf_forecasts';


-- add trigger for deletion from cdf_forecasts_groups table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_object_perm_on_cdf_forecasts_groups_delete AFTER DELETE ON arbiter_data.cdf_forecasts_groups
FOR EACH ROW DELETE FROM arbiter_data.permission_object_mapping WHERE object_id = OLD.id;


-- restrict fields that can be updated in cdf forecasts
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER limit_cdf_forecasts_singles_update BEFORE UPDATE ON arbiter_data.cdf_forecasts_singles
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify cdf forecast single object';
END;

CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER limit_cdf_forecasts_groups_update BEFORE UPDATE ON arbiter_data.cdf_forecasts_groups
FOR EACH ROW
BEGIN
    IF NEW.organization_id != OLD.organization_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify orgnization_id of cdf forecast object';
    ELSEIF NEW.site_id != OLD.site_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify site_id of cdf forecast object';
END IF;
END;



-- PROCEDURES
CREATE DEFINER = 'select_objects'@'localhost' FUNCTION get_constant_values (group_id BINARY(16))
RETURNS JSON
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE jsonout JSON;
    SET jsonout = (SELECT JSON_OBJECTAGG(BIN_TO_UUID(id, 1), constant_value) as constant_value FROM cdf_forecasts_singles
        WHERE cdf_forecast_group_id = group_id GROUP BY cdf_forecast_group_id);
    IF jsonout is NOT NULL THEN
        RETURN jsonout;
    ELSE
        RETURN JSON_OBJECT();
    END IF;
END;


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_cdf_forecasts_groups (IN auth0id VARCHAR(32))
COMMENT 'List all cdf forecast groups and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as forecast_id,
       get_organization_name(organization_id) as provider,
       BIN_TO_UUID(site_id, 1) as site_id,
       name, variable, issue_time_of_day, lead_time_to_start,
       interval_label, interval_length, run_length,
       interval_value_type, extra_parameters, axis,
       created_at, modified_at,
       get_constant_values(id) as constant_values
       FROM cdf_forecasts_groups WHERE id in (
           SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'cdf_forecasts');


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_cdf_forecasts_singles (IN auth0id VARCHAR(32))
COMMENT 'List all cdf forecast singletons and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(cfs.id, 1) as forecast_id, get_organization_name(cfg.organization_id) as provider,
       BIN_TO_UUID(cfg.site_id, 1) as site_id, BIN_TO_UUID(cfs.cdf_forecast_group_id, 1) as parent,
       cfg.name as name, cfg.variable as variable,
       cfg.issue_time_of_day as issue_time_of_day, cfg.lead_time_to_start as lead_time_to_start,
       cfg.interval_label as interval_label, cfg.interval_length as interval_length,
       cfg.run_length as run_length, cfg.interval_value_type as interval_value_type,
       cfg.extra_parameters as extra_parameters, cfg.axis as axis, cfs.created_at as created_at,
       cfs.constant_value as constant_value
FROM cdf_forecasts_groups as cfg, cdf_forecasts_singles as cfs WHERE cfg.id in (
     SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'cdf_forecasts')
AND cfs.cdf_forecast_group_id = cfg.id;


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
            BIN_TO_UUID(site_id, 1) as site_id, name, variable,
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
            BIN_TO_UUID(cfg.site_id, 1) as site_id, BIN_TO_UUID(cfs.cdf_forecast_group_id, 1) as parent,
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

CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_cdf_forecast_values (
IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP)
COMMENT 'Read cdf forecast values'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE groupid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET groupid = (SELECT cdf_forecast_group_id FROM cdf_forecasts_singles WHERE id = binid);
    SET allowed = (SELECT can_user_perform_action(auth0id, groupid, 'read_values'));
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as forecast_id, timestamp, value
        FROM arbiter_data.cdf_forecasts_values WHERE id = binid AND timestamp BETWEEN start AND end;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read cdf forecast values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


GRANT SELECT ON arbiter_data.cdf_forecasts_groups TO 'select_objects'@'localhost';
GRANT SELECT ON arbiter_data.cdf_forecasts_singles TO 'select_objects'@'localhost';
GRANT SELECT ON arbiter_data.cdf_forecasts_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_constant_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_cdf_forecasts_groups TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_cdf_forecasts_singles TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_cdf_forecasts_group TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_cdf_forecasts_single TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_cdf_forecast_values TO 'select_objects'@'localhost';


CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_cdf_forecasts_group (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN site_id CHAR(36), IN name VARCHAR(64), IN variable VARCHAR(32),
  IN issue_time_of_day VARCHAR(5), IN lead_time_to_start SMALLINT UNSIGNED, IN interval_label VARCHAR(32),
  IN interval_length SMALLINT UNSIGNED, IN run_length SMALLINT UNSIGNED, IN interval_value_type VARCHAR(32),
  IN extra_parameters TEXT, IN axis VARCHAR(1))
COMMENT 'Store an cdf forecast group object. User must be able to read site information.'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE binsiteid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE canreadsite BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'cdf_forecasts'));
    SET binsiteid = (SELECT UUID_TO_BIN(site_id, 1));
    IF allowed THEN
       SET canreadsite = (SELECT can_user_perform_action(auth0id, binsiteid, 'read'));
       IF canreadsite THEN
           SELECT get_user_organization(auth0id) INTO orgid;
           INSERT INTO arbiter_data.cdf_forecasts_groups (
               id, organization_id, site_id, name, variable, issue_time_of_day, lead_time_to_start,
               interval_label, interval_length, run_length, interval_value_type, extra_parameters, axis
           ) VALUES (
               UUID_TO_BIN(strid, 1), orgid, binsiteid, name, variable, issue_time_of_day,
               lead_time_to_start, interval_label, interval_length, run_length, interval_value_type,
               extra_parameters, axis);
       ELSE
           SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not have permission to read site', MYSQL_ERRNO = 1143;
       END IF;
    ELSE
       SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create cdf forecasts"',
       MYSQL_ERRNO = 1142;
    END IF;
END;

CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_cdf_forecasts_single (
  IN auth0id VARCHAR(32), IN strid CHAR(36), IN parent_id CHAR(36), IN constant_value FLOAT)
COMMENT 'Store an cdf forecast singleton object. User must be able to update cdf parent group information.'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE groupid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE canupdategroup BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'cdf_forecasts'));
    SET groupid = UUID_TO_BIN(parent_id, 1);
    IF allowed THEN
       SET canupdategroup = (SELECT can_user_perform_action(auth0id, groupid, 'update'));
       IF canupdategroup THEN
           INSERT INTO arbiter_data.cdf_forecasts_singles (
               id, cdf_forecast_group_id, constant_value
           ) VALUES (
               UUID_TO_BIN(strid, 1), groupid, constant_value);
       ELSE
           SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not have permission to update cdf group',
           MYSQL_ERRNO = 1143;
       END IF;
    ELSE
       SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create cdf forecasts"',
       MYSQL_ERRNO = 1142;
    END IF;
END;

CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_cdf_forecast_values (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN timestamp TIMESTAMP, IN value FLOAT)
COMMENT 'Store a single time, value, quality_flag row into cdf_forecast_values'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE groupid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET groupid = (SELECT cdf_forecast_group_id FROM cdf_forecasts_singles WHERE id = binid);
    SET allowed = (SELECT can_user_perform_action(auth0id, groupid, 'write_values'));
    IF allowed THEN
        INSERT INTO arbiter_data.cdf_forecasts_values (id, timestamp, value) VALUES (
            binid, timestamp, value) ON DUPLICATE KEY UPDATE value=value;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "write cdf forecast values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT INSERT ON arbiter_data.cdf_forecasts_groups TO 'insert_objects'@'localhost';
GRANT INSERT, SELECT (id, cdf_forecast_group_id) ON arbiter_data.cdf_forecasts_singles TO 'insert_objects'@'localhost';
GRANT INSERT, UPDATE ON arbiter_data.cdf_forecasts_values TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_cdf_forecasts_group TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_cdf_forecasts_single TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_cdf_forecast_values TO 'insert_objects'@'localhost';

CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_cdf_forecasts_group(
    IN auth0id VARCHAR(32), IN strid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'delete'));
    IF allowed THEN
        DELETE FROM arbiter_data.cdf_forecasts_groups WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "delete cdf forecast group"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_cdf_forecasts_single(
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Delete cdf forecast singleton if user can update parent cdf group and also delete it'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE groupid BINARY(16);
    DECLARE update_allowed BOOLEAN DEFAULT FALSE;
    DECLARE delete_allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET groupid = (SELECT cdf_forecast_group_id FROM cdf_forecasts_singles WHERE id = binid);
    SET update_allowed = (SELECT can_user_perform_action(auth0id, groupid, 'update'));
    SET delete_allowed = (SELECT can_user_perform_action(auth0id, groupid, 'delete'));
    IF update_allowed AND delete_allowed THEN
        DELETE FROM arbiter_data.cdf_forecasts_singles WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "delete cdf forecast single"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


GRANT DELETE, SELECT (id) ON arbiter_data.cdf_forecasts_groups TO 'delete_objects'@'localhost';
GRANT DELETE, SELECT (id, cdf_forecast_group_id) ON arbiter_data.cdf_forecasts_singles TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_cdf_forecasts_group TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_cdf_forecasts_single TO 'delete_objects'@'localhost';
