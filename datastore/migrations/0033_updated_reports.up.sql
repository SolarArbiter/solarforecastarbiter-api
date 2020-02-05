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
        SELECT BIN_TO_UUID(id,1) as id, BIN_TO_UUID(object_id, 1) as object_id,
            processed_values
        FROM arbiter_data.report_values WHERE report_id = binid AND (
            SELECT can_user_perform_action(auth0id, object_id, 'read_values'));
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read report values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.read_report_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_report_values TO 'apiuser'@'%';


SET @orgid = (SELECT UUID_TO_BIN('b76ab62e-4fe1-11e9-9e44-64006a511e6f', 1));
SET @userid = (SELECT UUID_TO_BIN('0c90950a-7cca-11e9-a81f-54bf64606445', 1));
SET @roleid = (SELECT id from arbiter_data.roles WHERE name = 'Test user role');
INSERT INTO arbiter_data.permissions (description, organization_id, action, object_type, applies_to_all) VALUES (
    'TESTREPORT read', @orgid, 'read', 'reports', TRUE), (
    'TESTREPORT read_values', @orgid, 'read_values', 'reports', TRUE), (
    'TESTREPORT write_values', @orgid, 'write_values', 'reports', TRUE), (
    'TESTREPORT create', @orgid, 'create', 'reports', TRUE), (
    'TESTREPORT delete', @orgid, 'delete', 'reports', TRUE);

INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) SELECT @roleid, id FROM arbiter_data.permissions WHERE description like 'TESTREPORT %';

INSERT INTO arbiter_data.reports (id, organization_id, name,
    report_parameters, raw_report, status, created_at, modified_at)
VALUES (UUID_TO_BIN('9f290dd4-42b8-11ea-abdf-f4939feddd82', 1), @orgid,
    'NREL MIDC OASIS GHI Forecast Analysis',
    '{"name": "NREL MIDC OASIS GHI Forecast Analysis", "start": "2019-04-01T07:00:00Z", "end": "2019-06-01T06:59:00Z", "metrics": ["mae", "rmse"], "filters": [{"quality_flags": ["USER FLAGGED"]}], "categories": ["total", "date"], "object_pairs": [{"observation": "123e4567-e89b-12d3-a456-426655440000", "forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3"}]}',
    '{"generated_at": "2019-07-01T12:00:00+00:00", "timezone": "Etc/GMT+8", "versions": [], "plots": null, "metrics": [], "processed_forecasts_observations": [], "messages": [{"message": "FAILED", "step": "dunno", "level": "error", "function": "fcn"}], "data_checksum": null}',
    'failed', '2020-01-22 13:48:00', '2020-01-22 13:50:00');

INSERT INTO arbiter_data.report_values (id, report_id, object_id, processed_values) VALUES (
    UUID_TO_BIN('a2b6ed14-42d0-11ea-aa3c-f4939feddd82', 1),
    UUID_TO_BIN('9f290dd4-42b8-11ea-abdf-f4939feddd82', 1),
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440000', 1),
    'superencodedvalues');
