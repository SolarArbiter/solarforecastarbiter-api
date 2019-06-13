ALTER TABLE arbiter_data.permissions CHANGE COLUMN object_type object_type ENUM('sites', 'aggregates', 'cdf_forecasts', 'forecasts', 'observations', 'users', 'roles', 'permissions', 'reports') NOT NULL;

-- create reports table
CREATE TABLE arbiter_data.reports(
    id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
    organization_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,
    report_parameters JSON NOT NULL,
    metrics JSON NOT NULL,

    PRIMARY KEY (id),
    FOREIGN KEY (organization_id)
        REFERENCES arbiter_data.organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

-- create table for storing reports values
CREATE TABLE arbiter_data.report_values(
    report_id BINARY(16) NOT NULL,
    object_id BINARY(16) NOT NULL,
    processed_values BLOB NOT NULL,
    
    KEY (report_id, object_id),
    FOREIGN KEY (report_id)
        REFERENCES arbiter_data.reports(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

-- Report READ PROCEDURES
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_reports (IN auth0id VARCHAR(32))
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as report_id,
       get_organization_name(orgnization_id) as provider
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
        SELECT BIN_TO_UUID(id, 1) as report_id, get_organization_name(organization_id) as provider
        FROM arbiter_data.reports where id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read report"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
               
GRANT SELECT ON arbiter_data.reports TO 'select_objects'@'localhost';
GRANT SELECT ON arbiter_data.report_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_report TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_reports TO 'select_objects'@'localhost';

-- Report STORE PROCEDURES
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_report (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN name VARCHAR(64),
    IN report_parameters JSON, IN metrics JSON)
MODIFIES SQL DATA SQL SECURITY DEFINER
COMMENT 'Store report metadata'
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET allowed = (SELECT user_can_create(auth0id, 'reports'));
    IF allowed THEN
        SELECT get_user_organization(auth0id) INTO orgid;
        INSERT INTO arbiter_data.reports (
            id, organization_id, name, report_parameters, metrics
        ) VALUES (
            UUID_TO_BIN(strid, 1), orgid, name, report_parameters, metrics);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "create cdf forecasts"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_report_values (
    IN auth0id VARCHAR(32), IN str_report_id CHAR(36), IN str_object_id CHAR(36),
    IN processedvalues BLOB)
MODIFIES SQL DATA SQL SECURITY DEFINER
COMMENT 'Store processed values for a report'
BEGIN
    DECLARE bin_report_id BINARY(16);
    DECLARE bin_object_id BINARY(16);
    DECLARE read_allowed BOOLEAN DEFAULT FALSE;
    DECLARE create_allowed BOOLEAN DEFAULT FALSE;
    SET bin_report_id = (SELECT UUID_TO_BIN(str_report_id, 1));
    SET bin_object_id = (SELECT UUID_TO_BIN(str_object_id, 1));
    SET read_allowed = (SELECT can_user_perform_action(auth0id, bin_report_id, 'reports'));
    SET create_allowed = (SELECT user_can_create(auth0id, bin_object_id, 'reports'));
    IF read_allowed and create_allowed THEN
        INSERT INTO arbiter_data.report_values (
            report_id, object_id, processed_values) VALUES (
            bin_report_id, bin_object_id, processed_values);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "store report values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT INSERT ON arbiter_data.reports TO 'insert_objects'@'localhost';
GRANT INSERT ON arbiter_data.report_values TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_report TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_report_values TO 'insert_objects'@'localhost';

CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_report (
    IN auth0id VARCHAR(31), IN strid CHAR(36))
COMMENT 'Delete report'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (UUID_TO_BIN(binid, 1));
    SET allowed = (SELECT UUID_TO_BIN(binid, 1));
    IF allowed THEN
        DELETE FROM arbiter_data.reports WHERE report_id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "delete report"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT DELETE on arbiter_data.reports TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_report TO 'delete_objects'@'localhost';
