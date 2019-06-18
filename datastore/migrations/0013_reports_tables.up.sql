ALTER TABLE arbiter_data.permissions CHANGE COLUMN object_type object_type ENUM('sites', 'aggregates', 'cdf_forecasts', 'forecasts', 'observations', 'users', 'roles', 'permissions', 'reports') NOT NULL;

-- create reports table
CREATE TABLE arbiter_data.reports(
    id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
    organization_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,
    report_parameters JSON NOT NULL,
    metrics JSON,
    status ENUM('pending', 'complete', 'failed') NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    FOREIGN KEY (organization_id)
        REFERENCES arbiter_data.organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

-- create table for storing reports values
CREATE TABLE arbiter_data.report_values(
    id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
    report_id BINARY(16) NOT NULL,
    object_id BINARY(16) NOT NULL,
    processed_values BLOB NOT NULL,
    
    PRIMARY KEY (report_id, id),
    KEY (object_id),
    FOREIGN KEY (report_id)
        REFERENCES arbiter_data.reports(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

-- Report READ PROCEDURES
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_reports (IN auth0id VARCHAR(32))
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as report_id, get_organization_name(organization_id) as provider,
       name, report_parameters, metrics, status, created_at, modified_at
       FROM arbiter_data.reports WHERE id in (
       SELECT object_id from user_objects where auth0_id = auth0id AND object_type = 'reports');


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_report (
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read report metadata'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as report_id, get_organization_name(organization_id) as provider,
        name, report_parameters, metrics, status, created_at, modified_at
        FROM arbiter_data.reports where id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read report"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_report_values (
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read processed report values of a single object'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed boolean DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = can_user_perform_action(auth0id, binid, 'read');
    IF allowed THEN
        SELECT BIN_TO_UUID(id,1) as id, BIN_TO_UUID(report_id, 1) as report_id,
        BIN_TO_UUID(object_id, 1) as object_id, processed_values
        FROM arbiter_data.report_values WHERE report_id = binid AND (
            SELECT can_user_perform_action(auth0id, object_id, 'read_values'));
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read report values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT SELECT ON arbiter_data.reports TO 'select_objects'@'localhost';
GRANT SELECT ON arbiter_data.report_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_report TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_report_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_reports TO 'select_objects'@'localhost';

-- Report STORE PROCEDURES
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

CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_report_values (
    IN auth0id VARCHAR(32), IN strid CHAR(36),IN str_report_id CHAR(36), IN str_object_id CHAR(36),
    IN processedvalues BLOB)
MODIFIES SQL DATA SQL SECURITY DEFINER
COMMENT 'Store processed values for a report'
BEGIN
    DECLARE binid BINARY(16);
    DECLARE bin_report_id BINARY(16);
    DECLARE bin_object_id BINARY(16);
    DECLARE create_allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET bin_object_id = (SELECT UUID_TO_BIN(str_object_id, 1));
    SET bin_report_id = (SELECT UUID_TO_BIN(str_report_id, 1));
    SET create_allowed = (SELECT can_user_perform_action(auth0id, bin_report_id, 'write_values'));
    IF create_allowed THEN
        INSERT INTO arbiter_data.report_values (
            id, report_id, object_id, processed_values) VALUES (
            binid, bin_report_id, bin_object_id, processedvalues)
        ON DUPLICATE KEY UPDATE processed_values = processedvalues;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "store report values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE set_report_metrics(
    IN auth0id VARCHAR(31), IN strid CHAR(36), IN new_metrics JSON)
COMMENT 'Update metrics field with json'
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'update'));
    IF allowed THEN
        UPDATE arbiter_data.reports SET metrics = new_metrics WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "set report status"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE set_report_status(
    IN auth0id VARCHAR(31), IN strid CHAR(36), IN new_status VARCHAR(16))
COMMENT 'Set the status of the report'
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'update'));
    IF allowed THEN
        UPDATE arbiter_data.reports SET status = new_status WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "set report status"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


GRANT INSERT, SELECT, UPDATE ON arbiter_data.reports TO 'insert_objects'@'localhost';
GRANT INSERT, UPDATE ON arbiter_data.report_values TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_report TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_report_values TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.set_report_metrics TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.set_report_status TO 'insert_objects'@'localhost';



-- Report delete procedure
CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_report (
    IN auth0id VARCHAR(31), IN strid CHAR(36))
COMMENT 'Delete report'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'delete'));
    IF allowed THEN
        DELETE FROM arbiter_data.reports WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "delete report"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT DELETE, SELECT(id) on arbiter_data.reports TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_report TO 'delete_objects'@'localhost';

-- add permission triggers for reports
GRANT SELECT, TRIGGER ON arbiter_data.reports TO 'permission_trig'@'localhost';
GRANT TRIGGER ON arbiter_data.report_values TO 'permission_trig'@'localhost';

-- add permissions triggers for reports
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER add_object_perm_on_report_permissions_insert AFTER INSERT ON arbiter_data.permissions
FOR EACH ROW PRECEDES add_object_perm_on_permissions_insert
BEGIN
    IF NEW.applies_to_all AND NEW.action != 'create' THEN
        IF NEW.object_type = 'reports' THEN
            INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
                SELECT NEW.id, id FROM arbiter_data.reports where organization_id = NEW.organization_id;
        END IF;
    END IF;
END;

-- add new reports to 'applies_to_all' reports permissions
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER add_object_perm_on_reports_insert AFTER INSERT ON arbiter_data.reports
FOR EACH ROW INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
    SELECT id, NEW.id FROM arbiter_data.permissions WHERE action != 'create' AND applies_to_all AND organization_id = NEW.organization_id AND object_type = 'reports';

-- remove any object permission mappings after report deletion
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_object_perm_on_report_delete AFTER DELETE ON arbiter_data.reports
FOR EACH ROW DELETE FROM arbiter_data.permission_object_mapping WHERE object_id = OLD.id;

-- restrict fields that may be updated
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER limit_reports_update BEFORE UPDATE ON arbiter_data.reports
FOR EACH ROW
BEGIN
    IF NEW.organization_id != OLD.organization_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify organization_id of report object';
    END IF;
END;

GRANT SELECT, DELETE ON arbiter_data.report_values TO 'permission_trig'@'localhost';
-- remove processed data when the orginal obs/fx/cdf is deleted
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_report_values_on_observation_delete AFTER DELETE ON arbiter_data.observations
FOR EACH ROW DELETE FROM arbiter_data.report_values WHERE object_id = OLD.id;

CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_report_values_on_forecast_delete AFTER DELETE ON arbiter_data.forecasts
FOR EACH ROW DELETE FROM arbiter_data.report_values WHERE object_id = OLD.id;

CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_report_values_on_cdf_forecast_delete AFTER DELETE ON arbiter_data.cdf_forecasts_groups
FOR EACH ROW DELETE FROM arbiter_data.report_values WHERE object_id = OLD.id;

-- Redefine permissions functions to add reports

-- function to get organization of any non-rbac object
DROP FUNCTION IF EXISTS get_nonrbac_object_organization;
CREATE DEFINER = 'select_objects'@'localhost' FUNCTION get_nonrbac_object_organization (
    object_id BINARY(16), object_type VARCHAR(32))
RETURNS BINARY(16)
COMMENT 'Return the id of the organization for the object'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    IF object_type = 'sites' THEN
        RETURN (SELECT organization_id FROM arbiter_data.sites WHERE id = object_id);
    ELSEIF object_type = 'observations' THEN
        RETURN (SELECT organization_id FROM arbiter_data.observations WHERE id = object_id);
    ELSEIF object_type = 'forecasts' THEN
        RETURN (SELECT organization_id FROM arbiter_data.forecasts WHERE id = object_id);
    ELSEIF object_type = 'cdf_forecasts' THEN
        RETURN (SELECT organization_id FROM arbiter_data.cdf_forecasts_groups WHERE id = object_id);
    ELSEIF object_type = 'reports' THEN
        RETURN (SELECT organization_id FROM arbiter_data.reports WHERE id = object_id);
    ELSE
        RETURN NULL;
    END IF;
END;

-- function to get organization of any object
DROP FUNCTION IF EXISTS get_object_organization;
CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_object_organization (
    object_id BINARY(16), object_type VARCHAR(32))
RETURNS BINARY(16)
COMMENT 'Return the id of the organization for the object'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    IF object_type in ('users', 'roles', 'permissions') THEN
        RETURN get_rbac_object_organization(object_id, object_type);
    ELSEIF object_type in ('sites', 'observations', 'forecasts', 'cdf_forecasts', 'reports') THEN
        RETURN get_nonrbac_object_organization(object_id, object_type);
    ELSE
        RETURN NULL;
    END IF;
END;

GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'select_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_nonrbac_object_organization TO 'select_objects'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_nonrbac_object_organization TO 'select_rbac'@'localhost';
