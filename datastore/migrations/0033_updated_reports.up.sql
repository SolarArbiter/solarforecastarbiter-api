ALTER TABLE arbiter_data.reports MODIFY COLUMN raw_reports JSON;


CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_report_metrics(
IN auth0id VARCHAR(31), IN strid CHAR(36), IN new_metrics JSON, IN new_raw_report JSON)
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
