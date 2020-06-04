DROP PROCEDURE update_site_zone_mapping_new_site;
DROP PROCEDURE update_site_zone_mapping_new_zone;
DROP TABLE site_zone_mapping;
DROP TABLE climate_zones;
DROP TRIGGER update_zone_mapping_on_site_insert;
DROP TRIGGER update_zone_mapping_on_site_update;
DROP USER 'climzones'@'localhost';
