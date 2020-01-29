ALTER TABLE arbiter_data.reports MODIFY COLUMN raw_report LONGBLOB;
ALTER TABLE arbiter_data.reports ADD COLUMN metrics JSON;

DROP PROCEDURE store_raw_report;

CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_report_metrics(
    IN auth0id VARCHAR(31), IN strid CHAR(36), IN new_metrics JSON, IN new_raw_report LONGBLOB)
COMMENT 'Update metrics field with json and raw_report with binary data'
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'update'));
    IF allowed THEN
        UPDATE arbiter_data.reports SET metrics = new_metrics, raw_report = new_raw_report
        WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "set report metrics"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.store_report_metrics TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_report_metrics TO 'apiuser'@'%';


DROP PROCEDURE read_report;

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
           name, report_parameters, metrics, raw_report, status, created_at, modified_at
        FROM arbiter_data.reports where id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read report"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.read_report TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_report TO 'apiuser'@'%';


DROP PROCEDURE list_reports;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_reports (IN auth0id VARCHAR(32))
READS SQL DATA SQL SECURITY DEFINER
    SELECT BIN_TO_UUID(id, 1) as report_id, get_organization_name(organization_id) as provider,
        name, report_parameters, metrics, status, created_at, modified_at
    FROM arbiter_data.reports WHERE id in (
        SELECT object_id from user_objects where auth0_id = auth0id AND object_type = 'reports');

GRANT EXECUTE ON PROCEDURE arbiter_data.list_reports TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_reports TO 'apiuser'@'%';

DROP PROCEDURE read_report_values;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_report_values (
IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read processed report values of a single object'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed boolean DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = can_user_perform_action(auth0id, binid, 'read_values');
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

GRANT EXECUTE ON PROCEDURE arbiter_data.read_report_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_report_values TO 'apiuser'@'%';



DELETE FROM arbiter_data.permissions WHERE description like 'TESTREPORT %';
DELETE FROM arbiter_data.reports WHERE id = UUID_TO_BIN('9f290dd4-42b8-11ea-abdf-f4939feddd82', 1);
