DROP PROCEDURE store_raw_report;
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_raw_report(
IN auth0id VARCHAR(31), IN strid CHAR(36), IN new_raw_report JSON, IN keep_report_values JSON)
COMMENT 'Update metrics field with json and raw_report with binary data'
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (can_user_perform_action(auth0id, binid, 'update') AND
        can_user_perform_action(auth0id, binid, 'write_values'));
    IF allowed THEN
        DELETE FROM arbiter_data.report_values WHERE report_id = binid AND id NOT IN (
            SELECT uuid_to_bin(jt.id, 1) FROM JSON_TABLE(
                keep_report_values, '$[*]' COLUMNS(id CHAR(36) PATH '$.id')) as jt);
        UPDATE arbiter_data.reports SET raw_report = new_raw_report
        WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "store raw report"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT SELECT(id, report_id), DELETE ON arbiter_data.report_values TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_raw_report TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_raw_report TO 'apiuser'@'%';
