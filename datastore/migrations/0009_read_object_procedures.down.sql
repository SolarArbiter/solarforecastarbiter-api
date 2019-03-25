REVOKE SELECT ON arbiter_data.observations_values FROM 'select_objects'@'localhost';
REVOKE SELECT ON arbiter_data.forecasts_values FROM 'select_objects'@'localhost';
REVOKE EXECUTE ON FUNCTION arbiter_data.can_user_perform_action FROM 'select_objects'@'localhost';
REVOKE EXECUTE ON PROCEDURE arbiter_data.read_site FROM 'select_objects'@'localhost';
REVOKE EXECUTE ON PROCEDURE arbiter_data.read_observation FROM 'select_objects'@'localhost';
REVOKE EXECUTE ON PROCEDURE arbiter_data.read_forecast FROM 'select_objects'@'localhost';
REVOKE EXECUTE ON PROCEDURE arbiter_data.read_observation_values FROM 'select_objects'@'localhost';
REVOKE EXECUTE ON PROCEDURE arbiter_data.read_forecast_values FROM 'select_objects'@'localhost';


DROP PROCEDURE read_site;
DROP PROCEDURE read_observation;
DROP PROCEDURE read_observation_values;
DROP PROCEDURE read_forecast;
DROP PROCEDURE read_forecast_values;
