DROP PROCEDURE store_raw_report;
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

REVOKE SELECT, DELETE ON arbiter_data.report_values FROM 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_raw_report TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_raw_report TO 'apiuser'@'%';
