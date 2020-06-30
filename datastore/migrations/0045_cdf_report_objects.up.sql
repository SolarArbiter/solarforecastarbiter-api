CREATE DEFINER = 'select_objects'@'localhost' FUNCTION is_read_values_any_allowed(
    auth0id VARCHAR(32), binid BINARY(16))
RETURNS BOOLEAN
COMMENT 'Return if read values of the object (forecast, observation, cdf forecast constant value) is allowed'
READS SQL DATA SQL SECURITY DEFINER
/* if groupid is null (no cdf singe) can_user_perform_action will be false */
RETURN can_user_perform_action(auth0id, binid, 'read_values') OR
       can_user_perform_action(auth0id, (SELECT cdf_forecast_group_id FROM cdf_forecasts_singles WHERE id = binid), 'read_values');

GRANT EXECUTE ON FUNCTION arbiter_data.is_read_values_any_allowed TO 'select_objects'@'localhost';

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
        FROM arbiter_data.report_values WHERE report_id = binid AND
            is_read_values_any_allowed(auth0id, object_id);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read report values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.read_report_values TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_report_values TO 'apiuser'@'%';


CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_report_values_on_cdf_forecast_single_delete AFTER DELETE ON arbiter_data.cdf_forecasts_singles
FOR EACH ROW DELETE FROM arbiter_data.report_values WHERE object_id = OLD.id;
GRANT TRIGGER ON arbiter_data.cdf_forecasts_singles TO 'permission_trig'@'localhost';

DROP TRIGGER validate_object_id_on_report_value_insert;
