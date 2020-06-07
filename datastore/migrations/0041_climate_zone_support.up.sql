CREATE USER 'climzones'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;

CREATE TABLE arbiter_data.climate_zones (
    name varchar(255) NOT NULL UNIQUE,
    g GEOMETRY NOT NULL SRID 4326,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (name),
    SPATIAL INDEX (g)
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;
-- could later add an organization here for user defined zones and ids for permissions

-- checking if a site is within a zone can take some time, so create a mapping between the sites
-- and zones and add triggers to keep it up to date.
CREATE TABLE arbiter_data.site_zone_mapping (
    site_id BINARY(16) NOT NULL,
    zone VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (site_id, zone),
    FOREIGN KEY (site_id)
        REFERENCES sites(id)
        ON DELETE CASCADE,
    -- also makes zone an index
    FOREIGN KEY (zone)
        REFERENCES climate_zones(name)
        ON DELETE CASCADE
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


GRANT INSERT, SELECT, DELETE ON arbiter_data.site_zone_mapping TO 'climzones'@'localhost';
GRANT SELECT, TRIGGER ON arbiter_data.sites TO 'climzones'@'localhost';
GRANT SELECT, TRIGGER ON arbiter_data.climate_zones TO 'climzones'@'localhost';

CREATE DEFINER = 'climzones'@'localhost' PROCEDURE arbiter_data.update_site_zone_mapping_new_site(
    siteid BINARY(16), latitude FLOAT, longitude FLOAT
)
COMMENT 'Update the site_zone_mapping table with the given site location'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DELETE FROM arbiter_data.site_zone_mapping WHERE site_id = siteid;
    INSERT INTO arbiter_data.site_zone_mapping (site_id, zone)
        SELECT siteid, name FROM arbiter_data.climate_zones WHERE ST_Within(
            ST_PointFromText(CONCAT('point(', latitude, ' ', longitude, ')'), 4326), g);
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.update_site_zone_mapping_new_site TO 'climzones'@'localhost';


CREATE DEFINER = 'climzones'@'localhost' PROCEDURE arbiter_data.update_site_zone_mapping_new_zone(
    newzone VARCHAR(255), g GEOMETRY
)
COMMENT 'Update the site_zone_mapping table with a new zone'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DELETE FROM arbiter_data.site_zone_mapping WHERE zone = newzone;
    INSERT INTO arbiter_data.site_zone_mapping (site_id, zone)
        SELECT id, newzone FROM arbiter_data.sites WHERE ST_Within(
            ST_PointFromText(CONCAT('point(', latitude, ' ', longitude, ')'), 4326), g);
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.update_site_zone_mapping_new_zone TO 'climzones'@'localhost';


CREATE DEFINER = 'climzones'@'localhost' TRIGGER update_zone_mapping_on_site_insert AFTER INSERT on arbiter_data.sites
FOR EACH ROW
CALL arbiter_data.update_site_zone_mapping_new_site(NEW.id, NEW.latitude, NEW.longitude);

CREATE DEFINER = 'climzones'@'localhost' TRIGGER update_zone_mapping_on_site_update AFTER UPDATE on arbiter_data.sites
FOR EACH ROW
CALL arbiter_data.update_site_zone_mapping_new_site(NEW.id, NEW.latitude, NEW.longitude);


CREATE DEFINER = 'climzones'@'localhost' TRIGGER update_zone_mapping_on_zone_insert AFTER INSERT on arbiter_data.climate_zones
FOR EACH ROW
CALL arbiter_data.update_site_zone_mapping_new_zone(NEW.name, NEW.g);

CREATE DEFINER = 'climzones'@'localhost' TRIGGER update_zone_mapping_on_zone_update AFTER UPDATE on arbiter_data.climate_zones
FOR EACH ROW
CALL arbiter_data.update_site_zone_mapping_new_zone(NEW.name, NEW.g);

-- foreign keys take care of deletion

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
               dc_loss_factor, ac_loss_factor, created_at, modified_at,
               IFNULL(
                   (SELECT JSON_ARRAYAGG(zone) FROM arbiter_data.site_zone_mapping WHERE site_id = id),
                   JSON_ARRAY()
               ) AS climate_zones
        FROM arbiter_data.sites WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read site"',
        MYSQL_ERRNO = 1142;
    END IF;
END;
GRANT SELECT ON arbiter_data.site_zone_mapping TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_site TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_site TO 'apiuser'@'%';


DROP PROCEDURE list_sites;
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_sites (IN auth0id VARCHAR(32))
COMMENT 'List all sites and associated metadata that the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as site_id, get_organization_name(organization_id) as provider,
    name, latitude, longitude, elevation, timezone, extra_parameters, ac_capacity, dc_capacity,
    temperature_coefficient, tracking_type, surface_tilt, surface_azimuth, axis_tilt,
    axis_azimuth, ground_coverage_ratio, backtrack, max_rotation_angle,
    dc_loss_factor, ac_loss_factor, created_at, modified_at,
    IFNULL(
        (SELECT JSON_ARRAYAGG(zone) FROM arbiter_data.site_zone_mapping WHERE site_id = id),
        JSON_ARRAY()
    ) AS climate_zones
FROM arbiter_data.sites WHERE id in (
    SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'sites');

GRANT EXECUTE ON PROCEDURE arbiter_data.list_sites TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_sites TO 'apiuser'@'%';


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_sites_in_zone(
    IN auth0id VARCHAR(32), IN thezone VARCHAR(255)
)
COMMENT 'List all sites within the climate zone that the user can read'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    IF ISNULL(thezone) OR thezone = '' THEN
        SELECT BIN_TO_UUID(id, 1) as site_id, get_organization_name(organization_id) as provider,
            name, latitude, longitude, elevation, timezone, extra_parameters, ac_capacity, dc_capacity,
            temperature_coefficient, tracking_type, surface_tilt, surface_azimuth, axis_tilt,
            axis_azimuth, ground_coverage_ratio, backtrack, max_rotation_angle,
            dc_loss_factor, ac_loss_factor, created_at, modified_at, JSON_ARRAY() as climate_zones
        FROM arbiter_data.sites WHERE id IN (
            SELECT object_id from user_objects WHERE auth0_id = @auth0id AND object_type = 'sites'
        ) AND id NOT IN (
            SELECT site_id FROM arbiter_data.site_zone_mapping
        );
    ELSE
        SELECT BIN_TO_UUID(id, 1) as site_id, get_organization_name(organization_id) as provider,
            name, latitude, longitude, elevation, timezone, extra_parameters, ac_capacity, dc_capacity,
            temperature_coefficient, tracking_type, surface_tilt, surface_azimuth, axis_tilt,
            axis_azimuth, ground_coverage_ratio, backtrack, max_rotation_angle,
            dc_loss_factor, ac_loss_factor, created_at, modified_at,
            IFNULL(
                (SELECT JSON_ARRAYAGG(zone) FROM arbiter_data.site_zone_mapping WHERE site_id = id),
                JSON_ARRAY()
            ) AS climate_zones -- still include other zones
        FROM arbiter_data.sites WHERE id in (
            SELECT object_id from user_objects WHERE auth0_id = auth0id AND object_type = 'sites'
        ) AND id IN (
            SELECT site_id FROM arbiter_data.site_zone_mapping WHERE zone = thezone
        );
    END IF;
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.list_sites_in_zone TO 'select_objects'@'localhost';


CREATE DEFINER = 'select_objects'@'localhost' FUNCTION arbiter_data.find_climate_zones(
    latitude FLOAT, longitude FLOAT
)
RETURNS JSON
COMMENT 'Return a JSON array of the climate zones the lat,lon point is within'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE outp JSON;
    SELECT JSON_ARRAYAGG(name) INTO outp FROM arbiter_data.climate_zones WHERE ST_Within(
        ST_PointFromText(CONCAT('point(', latitude, ' ', longitude, ')'), 4326), g);
    IF ISNULL(outp) THEN
        RETURN JSON_ARRAY();
    ELSE
        RETURN outp;
    END IF;
END;
GRANT SELECT ON arbiter_data.climate_zones TO 'select_objects'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.find_climate_zones TO 'select_objects'@'localhost';

-- set @testpoint = st_pointfromtext('point(42.43140199881 -105.28391000016)', 4326);
-- also tests site outside climeate zones
-- get zones as geojson

CREATE DEFINER = 'select_objects'@'localhost' FUNCTION massage_geo_json(g JSON, properties JSON)
RETURNS JSON
COMMENT 'Transformas a GeometryCollection into a FeatureCollection and adds the properties to each Feature'
READS SQL DATA SQL SECURITY DEFINER
RETURN (SELECT JSON_OBJECT(
    'type', 'FeatureCollection', 'crs', crs, 'features', JSON_ARRAYAGG(
        JSON_OBJECT('geometry', geo, 'type', 'Feature', 'properties', properties)
    )
) FROM JSON_TABLE(g, '$' COLUMNS (
    crs JSON PATH '$.crs',
    NESTED PATH '$.geometries[*]' COLUMNS (
        geo JSON PATH '$'))
) AS jt GROUP BY crs); -- will require a mysql upgrade

GRANT EXECUTE ON FUNCTION massage_geo_json TO 'select_objects'@'localhost';


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE arbiter_data.read_climate_zone(
    IN thezone VARCHAR(255)
)
COMMENT 'Return the reference climate zone as GeoJSON'
READS SQL DATA SQL SECURITY DEFINER
SELECT massage_geo_json(ST_AsGeoJSON(g, 8, 4), JSON_OBJECT('Name', name))
FROM arbiter_data.climate_zones WHERE name = thezone;

GRANT EXECUTE ON PROCEDURE arbiter_data.read_climate_zone TO 'select_objects'@'localhost';


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE arbiter_data.list_climate_zones()
COMMENT 'Return a list of climate zones w/o the geojson'
READS SQL DATA SQL SECURITY DEFINER
SELECT name, created_at, modified_at FROM arbiter_data.climate_zones;

GRANT EXECUTE ON PROCEDURE arbiter_data.list_climate_zones TO 'select_objects'@'localhost';
