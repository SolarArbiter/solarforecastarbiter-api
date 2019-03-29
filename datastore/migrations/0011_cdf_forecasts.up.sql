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
    organization_id BINARY(16) NOT NULL,
    cdf_forecast_group_id BINARY(16) NOT NULL,
    constant_value FLOAT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE (cdf_forecast_group_id, constant_value),
    FOREIGN KEY (organization_id)
        REFERENCES arbiter_data.organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
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
GRANT SELECT, TRIGGER ON arbiter_data.cdf_forecasts_singles TO 'permission_trig'@'localhost';

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
    IF NEW.organization_id != OLD.organization_id OR NEW.cdf_forecast_group_id != OLD.cdf_forecast_group_id
       OR NEW.constant_value != OLD.constant_value THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify cdf forecast single object';
    END IF;
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

-- Create procedure to return list of cdf forecasts a user can read
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_cdf_forecasts_groups (IN auth0id VARCHAR(32))
COMMENT 'List all cdf forecast groups and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(cfg.id, 1) as forecast_id, get_organization_name(cfg.organization_id) as provider,
       BIN_TO_UUID(cfg.site_id, 1) as site_id, cfg.name as name, cfg.variable as variable,
       cfg.issue_time_of_day as issue_time_of_day, cfg.lead_time_to_start as lead_time_to_start,
       cfg.interval_label as interval_label, cfg.interval_length as interval_length,
       cfg.run_length as run_length, cfg.interval_value_type as interval_value_type,
       cfg.extra_parameters as extra_parameters, cfg.axis as axis, cfg.created_at as created_at,
       cfg.modified_at as modified_at, JSON_OBJECTAGG(BIN_TO_UUID(cfs.id, 1), cfs.constant_value) as constant_values
FROM cdf_forecasts_groups as cfg, cdf_forecasts_singles as cfs WHERE cfg.id in (
     SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'cdf_forecasts')
     AND cfs.cdf_forecast_group_id = cfg.id
GROUP BY cfg.id;


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
        SELECT BIN_TO_UUID(cfg.id, 1) as forecast_id, get_organization_name(cfg.organization_id) as provider,
            BIN_TO_UUID(cfg.site_id, 1) as site_id, cfg.name as name, cfg.variable as variable,
            cfg.issue_time_of_day as issue_time_of_day, cfg.lead_time_to_start as lead_time_to_start,
            cfg.interval_label as interval_label, cfg.interval_length as interval_length,
            cfg.run_length as run_length, cfg.interval_value_type as interval_value_type,
            cfg.extra_parameters as extra_parameters, cfg.axis as axis, cfg.created_at as created_at,
            cfg.modified_at as modified_at, JSON_OBJECTAGG(BIN_TO_UUID(cfs.id, 1), cfs.constant_value) as constant_values
        FROM cdf_forecasts_groups as cfg, cdf_forecasts_singles as cfs WHERE cfg.id = binid AND cfs.cdf_forecast_group_id = cfg.id
        GROUP BY cfg.id;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read cdf forecast group"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


GRANT SELECT ON arbiter_data.cdf_forecasts_groups TO 'select_objects'@'localhost';
GRANT SELECT ON arbiter_data.cdf_forecasts_singles TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_cdf_forecasts_groups TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_cdf_forecasts_group TO 'select_objects'@'localhost';
