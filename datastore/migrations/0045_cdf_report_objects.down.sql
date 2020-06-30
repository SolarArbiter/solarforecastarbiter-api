DROP FUNCTION is_read_values_any_allowed;

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

DROP TRIGGER remove_report_values_on_cdf_forecast_single_delete;

CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER validate_object_id_on_report_value_insert BEFORE INSERT ON report_values
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT * FROM cdf_forecasts_singles WHERE id = New.object_id) THEN
        SIGNAL SQLSTATE 'HY000' SET MESSAGE_TEXT = 'Report value object_id must identify observation, forecast or cdf forecast group',
        MYSQL_ERRNO = 1210;
    END IF;
END;
