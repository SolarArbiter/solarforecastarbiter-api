-- add trigger for before deletion from sites table blocking on existing forecast
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER fail_on_site_delete_if_forecast BEFORE DELETE ON arbiter_data.sites
FOR EACH ROW
BEGIN
    DECLARE fxexists BOOLEAN;
    SET fxexists = (
        SELECT 1 FROM forecasts WHERE site_id = OLD.id
    );
    IF fxexists IS NOT NULL AND fxexists THEN
        SIGNAL SQLSTATE '23000' SET MESSAGE_TEXT = 'Site cannot be deleted, a forecast still references it.', MYSQL_ERRNO = 1451;
    END IF;
END;


-- restrict fields that can be updated in forecasts
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER limit_sites_update BEFORE UPDATE ON arbiter_data.sites
FOR EACH ROW
BEGIN
    IF NEW.organization_id != OLD.organization_id THEN
       SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify orgnization_id of site object';
    END IF;
END;


-- restrict fields that can be updated in forecasts
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER limit_forecasts_update BEFORE UPDATE ON arbiter_data.forecasts
FOR EACH ROW
BEGIN
    IF NEW.organization_id != OLD.organization_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify orgnization_id of forecast object';
    ELSEIF NEW.site_id != OLD.site_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify site_id of forecast object';
    END IF;
END;


-- restrict fields that can be updated in observations
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER limit_observations_update BEFORE UPDATE ON arbiter_data.observations
FOR EACH ROW
BEGIN
    IF NEW.organization_id != OLD.organization_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify orgnization_id of observation object';
    ELSEIF NEW.site_id != OLD.site_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot modify site_id of observation object';
    END IF;
END;


-- add trigger to fail on aggregate delete if forecast references it
/*CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER fail_on_aggregate_delete_if_forecast BEFORE DELETE ON arbiter_data.aggregates
FOR EACH ROW*/
