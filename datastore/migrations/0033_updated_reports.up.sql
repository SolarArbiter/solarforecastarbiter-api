ALTER TABLE arbiter_data.reports MODIFY COLUMN raw_report JSON;
ALTER TABLE arbiter_data.reports DROP COLUMN metrics;

DROP PROCEDURE store_report_metrics;

CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_raw_report(
IN auth0id VARCHAR(31), IN strid CHAR(36), IN new_raw_report JSON)
COMMENT 'Update metrics field with json and raw_report with binary data'
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'update'));
    IF allowed THEN
        UPDATE arbiter_data.reports SET raw_report = new_raw_report
        WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "store raw report"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.store_raw_report TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_raw_report TO 'apiuser'@'%';


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
            name, report_parameters, raw_report, status, created_at, modified_at
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
        name, report_parameters, status, created_at, modified_at
    FROM arbiter_data.reports WHERE id in (
        SELECT object_id from user_objects where auth0_id = auth0id AND object_type = 'reports');

GRANT EXECUTE ON PROCEDURE arbiter_data.list_reports TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_reports TO 'apiuser'@'%';
