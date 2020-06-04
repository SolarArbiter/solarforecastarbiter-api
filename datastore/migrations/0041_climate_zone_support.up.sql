CREATE USER 'climzones'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;

CREATE TABLE arbiter_data.climate_zones (
    name varchar(255) UNIQUE,
    g GEOMETRY NOT NULL SRID 4326,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;
-- could later add an organization here for user defined zones

-- checking if a site is within a zone can take some time, so create a mapping between the sites
-- and zones and add triggers to keep it up to date
CREATE TABLE arbiter_data.site_zone_mapping (
    site_id BINARY(16) NOT NULL,
    zone VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY (site_id, zone),
    FOREIGN KEY (site_id)
        REFERENCES sites(id)
        ON DELETE CASCADE,
    -- also makes zone an index
    FOREIGN KEY (zone)
        REFERENCES climate_zones(name)
        ON DELETE CASCADE
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


GRANT INSERT, SELECT ON arbiter_data.site_zone_mapping TO 'climzones'@'localhost';
GRANT SELECT(id, latitude, longitude), TRIGGER ON arbiter_data.sites TO 'climzones'@'localhost';
GRANT SELECT, TRIGGER ON arbiter_data.climate_zones TO 'climzones'@'localhost';

CREATE DEFINER = 'climzones'@'localhost' PROCEDURE update_site_zone_mapping_new_site(
    site_id BINARY(16), latitude FLOAT, longitude FLOAT
)
COMMENT 'Update the site_zone_mapping table with the given site location'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE newzone VARCHAR(255);
    -- limits on the first zone if there are multiple
    SET newzone = (SELECT name FROM climate_zones WHERE ST_Within(
        ST_PointFromText(CONCAT('point(', latitude, ' ', longitude, ')'), 4326), g)
        LIMIT 1);
    INSERT IGNORE INTO arbiter_data.site_zone_mapping (site_id, zone) VALUES (site_id, newzone);
END;
GRANT EXECUTE ON PROCEDURE arbiter_data.update_site_zone_mapping_new_site TO 'climzones'@'localhost';


CREATE DEFINER = 'climzones'@'localhost' PROCEDURE update_site_zone_mapping_new_zone(
    newzone VARCHAR(255), g GEOMETRY
)
COMMENT 'Update the site_zone_mapping table with a new zone'
MODIFIES SQL DATA SQL SECURITY DEFINER
INSERT IGNORE INTO arbiter_data.site_zone_mapping (site_id, zone)
    SELECT id, newzone FROM sites WHERE ST_Within(ST_PointFromText(CONCAT('point(', latitude, ' ', longitude, ')'), 4326), g);
GRANT EXECUTE ON PROCEDURE arbiter_data.update_site_zone_mapping_new_zone TO 'climzones'@'localhost';


CREATE DEFINER = 'climzones'@'localhost' TRIGGER update_zone_mapping_on_site_insert AFTER INSERT on arbiter_data.sites
FOR EACH ROW
CALL update_site_zone_mapping_new_site(NEW.id, NEW.latitude, NEW.longitude);

CREATE DEFINER = 'climzones'@'localhost' TRIGGER update_zone_mapping_on_site_update AFTER UPDATE on arbiter_data.sites
FOR EACH ROW
CALL update_site_zone_mapping_new_site(NEW.id, NEW.latitude, NEW.longitude);


CREATE DEFINER = 'climzones'@'localhost' TRIGGER update_zone_mapping_on_zone_insert AFTER INSERT on arbiter_data.climate_zones
FOR EACH ROW
CALL update_site_zone_mapping_new_zone(NEW.name, new.g);

CREATE DEFINER = 'climzones'@'localhost' TRIGGER update_zone_mapping_on_zone_update AFTER UPDATE on arbiter_data.climate_zones
FOR EACH ROW
CALL update_site_zone_mapping_new_zone(NEW.name, new.g);

-- foreign keys take care of deletion
-- set @testpoint = st_pointfromtext('point(42.43140199881 -105.28391000016)', 4326);
-- also tests site outside climeate zones
