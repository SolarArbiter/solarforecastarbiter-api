DROP FUNCTION find_climate_zones;
DROP PROCEDURE list_sites;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_sites (IN auth0id VARCHAR(32))
COMMENT 'List all sites and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as site_id, get_organization_name(organization_id) as provider,
    name, latitude, longitude, elevation, timezone, extra_parameters, ac_capacity, dc_capacity,
    temperature_coefficient, tracking_type, surface_tilt, surface_azimuth, axis_tilt,
    axis_azimuth, ground_coverage_ratio, backtrack, max_rotation_angle,
    dc_loss_factor, ac_loss_factor, created_at, modified_at
FROM arbiter_data.sites WHERE id in (
    SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'sites');
GRANT EXECUTE ON PROCEDURE arbiter_data.list_sites TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_sites TO 'apiuser'@'%';

DROP PROCEDURE read_site;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_site (
    IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read site metadata'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as site_id, get_organization_name(organization_id) as provider,
               name, latitude, longitude, elevation, timezone, extra_parameters, ac_capacity,
               dc_capacity, temperature_coefficient, tracking_type, surface_tilt, surface_azimuth,
               axis_tilt, axis_azimuth, ground_coverage_ratio, backtrack, max_rotation_angle,
               dc_loss_factor, ac_loss_factor, created_at, modified_at
        FROM arbiter_data.sites WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read site"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.read_site TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_site TO 'apiuser'@'%';
DROP TRIGGER update_zone_mapping_on_site_insert;
DROP TRIGGER update_zone_mapping_on_site_update;
DROP TRIGGER update_zone_mapping_on_zone_insert;
DROP TRIGGER update_zone_mapping_on_zone_update;
DROP PROCEDURE update_site_zone_mapping_new_site;
DROP PROCEDURE update_site_zone_mapping_new_zone;
DROP TABLE site_zone_mapping;
DROP TABLE climate_zones;
DROP USER 'climzones'@'localhost';
