SET @orgid = (SELECT UUID_TO_BIN('b76ab62e-4fe1-11e9-9e44-64006a511e6f', 1));

INSERT INTO arbiter_data.organizations (name, id, accepted_tou) VALUES (
    'Organization 1', @orgid, TRUE);

SET @userid = (SELECT UUID_TO_BIN('0c90950a-7cca-11e9-a81f-54bf64606445', 1));
INSERT INTO arbiter_data.users (id, auth0_id, organization_id) VALUES (
       @userid, 'auth0|5be343df7025406237820b85', @orgid);


SET @roleid = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES (
    'Test user role', 'Role for the test user to read, create, delete test objects',
    @roleid, @orgid);

INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (@userid, @roleid);

INSERT INTO arbiter_data.sites (
    id, organization_id, name, latitude, longitude, elevation, timezone, extra_parameters,
    created_at, modified_at
) VALUES (
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    @orgid,
    'Weather Station', 42.19, -122.7, 595.0, 'Etc/GMT+8',
    '{"network_api_abbreviation": "AS","network": "University of Oregon SRML","network_api_id": "94040"}',
    TIMESTAMP('2019-03-01 11:44:38'), TIMESTAMP('2019-03-01 11:44:38')
), (
    UUID_TO_BIN('d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a', 1),
    @orgid,
    'Weather Station 1', 32.22969, -110.95534, 786.0, 'America/Phoenix', '{"network": "NREL MIDC"}',
    TIMESTAMP('2019-03-01 11:44:44'), TIMESTAMP('2019-03-01 11:44:44')
);


INSERT INTO arbiter_data.permissions (description, organization_id, action, object_type, applies_to_all) VALUES (
    'Read all sites', @orgid, 'read', 'sites', TRUE), (
    'Read all forecasts', @orgid, 'read', 'forecasts', TRUE), (
    'Read all cdf forecasts', @orgid, 'read', 'cdf_forecasts', TRUE), (
    'Read all observations', @orgid, 'read', 'observations', TRUE), (
    'Read all reports', @orgid, 'read', 'reports', TRUE), (
    'Read all forecast values', @orgid, 'read_values', 'forecasts', TRUE), (
    'Read all cdf forecast values', @orgid, 'read_values', 'cdf_forecasts', TRUE), (
    'Read all observation values', @orgid, 'read_values', 'observations', TRUE), (
    'Read all report values', @orgid, 'read_values', 'reports', TRUE), (
    'Create all sites', @orgid, 'create', 'sites', TRUE), (
    'Create all forecasts', @orgid, 'create', 'forecasts', TRUE), (
    'Create all cdf forecasts', @orgid, 'create', 'cdf_forecasts', TRUE), (
    'Create all observations', @orgid, 'create', 'observations', TRUE), (
    'Create all reports', @orgid, 'create', 'reports', TRUE), (
    'Delete all sites', @orgid, 'delete', 'sites', TRUE), (
    'Delete all forecasts', @orgid, 'delete', 'forecasts', TRUE), (
    'Delete all cdf forecasts', @orgid, 'delete', 'cdf_forecasts', TRUE), (
    'Delete all observations', @orgid, 'delete', 'observations', TRUE), (
    'Delete all reports', @orgid, 'delete', 'reports', TRUE), (
    'Delete all forecast values', @orgid, 'delete_values', 'forecasts', TRUE), (
    'Delete all cdf forecast values', @orgid, 'delete_values', 'cdf_forecasts', TRUE), (
    'Delete all observation values', @orgid, 'delete_values', 'observations', TRUE), (
    'Write forecast values', @orgid, 'write_values', 'forecasts', TRUE), (
    'Write cdf forecast values', @orgid, 'write_values', 'cdf_forecasts', TRUE), (
    'Write observation values', @orgid, 'write_values', 'observations', TRUE), (
    'Write report values', @orgid, 'write_values', 'reports', TRUE), (
    'update reports', @orgid, 'update', 'reports', TRUE), (
    'update cdf group', @orgid, 'update', 'cdf_forecasts', TRUE);

INSERT INTO arbiter_data.permissions (description, organization_id, action, object_type, applies_to_all) VALUES (
    'Read Roles', @orgid, 'read', 'roles', TRUE), (
    'Read Users', @orgid, 'read', 'users', TRUE), (
    'Read Permissions', @orgid, 'read', 'permissions', TRUE), (
    'Create Roles', @orgid, 'create', 'roles', TRUE), (
    'Create Permissions', @orgid, 'create', 'permissions', TRUE), (
    'Update Roles', @orgid, 'update', 'roles', TRUE), (
    'Update User', @orgid, 'update', 'users', TRUE), (
    'Update Permissions', @orgid, 'update', 'permissions', TRUE), (
    'Delete Roles', @orgid, 'delete', 'roles', TRUE), (
    'Delete Permissions', @orgid, 'delete', 'permissions', TRUE);

INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) SELECT @roleid, id FROM arbiter_data.permissions WHERE organization_id = @orgid;


INSERT INTO arbiter_data.sites (
    id, organization_id, name, latitude, longitude, elevation, timezone, extra_parameters,
    ac_capacity, dc_capacity, temperature_coefficient, tracking_type, surface_tilt, surface_azimuth,
    ac_loss_factor, dc_loss_factor, created_at, modified_at
) VALUES (
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440002', 1),
    @orgid,
    'Power Plant 1', 43.73403, -96.62328, 786.0, 'Etc/GMT+6', '', 0.015, 0.015,
    -0.002, 'fixed', 45.0, 180, 0, 0,
    TIMESTAMP('2019-03-01 11:44:46'), TIMESTAMP('2019-03-01 11:44:46')
);


INSERT INTO arbiter_data.forecasts (
    id, organization_id, site_id, name, variable, issue_time_of_day, lead_time_to_start,
    interval_label, interval_length, run_length, interval_value_type, extra_parameters,
    created_at, modified_at
) VALUES (
    UUID_TO_BIN('11c20780-76ae-4b11-bef1-7a75bdc784e3', 1),
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    'DA GHI', 'ghi', '06:00', 60, 'beginning', 5, 1440, 'interval_mean', '',
    TIMESTAMP('2019-03-01 11:55:37'), TIMESTAMP('2019-03-01 11:55:37')
), (
    UUID_TO_BIN('f8dd49fa-23e2-48a0-862b-ba0af6dec276', 1),
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440002', 1),
    'HA Power', 'ac_power', '12:00', 60, 'beginning', 1, 60, 'interval_mean', '',
    TIMESTAMP('2019-03-01 11:55:38'), TIMESTAMP('2019-03-01 11:55:38')
);


INSERT INTO arbiter_data.observations (
    id, organization_id, site_id, name, variable, interval_label,  interval_length, interval_value_type,
    uncertainty, extra_parameters, created_at, modified_at
) VALUES (
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440000', 1),
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    'GHI Instrument 1', 'ghi', 'beginning', 5, 'interval_mean', 0.10,
    '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer", "network": "UO SRML"}',
    TIMESTAMP('2019-03-01 12:01:39'), TIMESTAMP('2019-03-01 12:01:39')
), (
    UUID_TO_BIN('9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f', 1),
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    'DHI Instrument 1', 'dhi', 'beginning', 5, 'interval_mean', 0.10,
    '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer", "network": "UO SRML"}',
    TIMESTAMP('2019-03-01 12:01:43'), TIMESTAMP('2019-03-01 12:01:43')
), (
    UUID_TO_BIN('9ce9715c-bd91-47b7-989f-50bb558f1eb9', 1),
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    'DNI Instrument 2', 'dni', 'beginning', 5, 'interval_mean', 0.10,
    '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer", "network": "UO SRML"}',
    TIMESTAMP('2019-03-01 12:01:48'), TIMESTAMP('2019-03-01 12:01:48')
), (
    UUID_TO_BIN('e0da0dea-9482-4073-84de-f1b12c304d23', 1),
    @orgid,
    UUID_TO_BIN('d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a', 1),
    'GHI Instrument 2', 'ghi', 'beginning', 5, 'interval_mean', 0.10,
    '{"instrument": "Kipp & Zonen CMP 22 Pyranometer", "network": "UO SRML"}',
    TIMESTAMP('2019-03-01 12:01:55'), TIMESTAMP('2019-03-01 12:01:55')
), (
    UUID_TO_BIN('b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2', 1),
    @orgid,
    UUID_TO_BIN('d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a', 1),
    'Sioux Falls, ghi', 'ghi', 'beginning', 5, 'interval_mean', 0.10,
    '{"instrument": "Kipp & Zonen CMP 22 Pyranometer", "network": "NOAA"}',
    TIMESTAMP('2019-03-01 12:02:38'), TIMESTAMP('2019-03-01 12:02:38')
);


SET @cfg0 = UUID_TO_BIN('ef51e87c-50b9-11e9-8647-d663bd873d93', 1);
SET @cfg0time = TIMESTAMP('2019-03-02 14:55:37');
SET @cfg1 = UUID_TO_BIN('058b182a-50ba-11e9-8647-d663bd873d93', 1);
SET @cfg1time = TIMESTAMP('2019-03-02 14:55:38');
INSERT INTO arbiter_data.cdf_forecasts_groups (
    id, organization_id, site_id, name, variable, issue_time_of_day, lead_time_to_start,
    interval_label, interval_length, run_length, interval_value_type, extra_parameters,
    created_at, modified_at, axis
) VALUES (
    @cfg0,
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    'DA GHI', 'ghi', '06:00', 60, 'beginning', 5, 1440, 'interval_mean', '',
    @cfg0time, @cfg0time, 'y'
), (
    @cfg1,
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440002', 1),
    'HA Power', 'ac_power', '12:00', 60, 'beginning', 1, 60, 'interval_mean', '',
    @cfg1time, @cfg1time, 'x'
);



INSERT INTO arbiter_data.cdf_forecasts_singles (id, cdf_forecast_group_id, constant_value, created_at)
VALUES (
     UUID_TO_BIN('633f9396-50bb-11e9-8647-d663bd873d93', 1), @cfg0, 5.0, @cfg0time), (
     UUID_TO_BIN('633f9864-50bb-11e9-8647-d663bd873d93', 1), @cfg0, 20.0, @cfg0time), (
     UUID_TO_BIN('633f9b2a-50bb-11e9-8647-d663bd873d93', 1), @cfg0, 50.0, @cfg0time), (
     UUID_TO_BIN('633f9d96-50bb-11e9-8647-d663bd873d93', 1), @cfg0, 80.0, @cfg0time), (
     UUID_TO_BIN('633fa548-50bb-11e9-8647-d663bd873d93', 1), @cfg0, 95.0, @cfg0time), (
     UUID_TO_BIN('633fa94e-50bb-11e9-8647-d663bd873d93', 1), @cfg1, 0.0, @cfg1time), (
     UUID_TO_BIN('633fabec-50bb-11e9-8647-d663bd873d93', 1), @cfg1, 5.0, @cfg1time), (
     UUID_TO_BIN('633fae62-50bb-11e9-8647-d663bd873d93', 1), @cfg1, 10.0, @cfg1time), (
     UUID_TO_BIN('633fb114-50bb-11e9-8647-d663bd873d93', 1), @cfg1, 15.0, @cfg1time), (
     UUID_TO_BIN('633fb3a8-50bb-11e9-8647-d663bd873d93', 1), @cfg1, 20.0, @cfg1time);




CREATE USER 'apiuser'@'%' IDENTIFIED BY 'thisisaterribleandpublicpassword';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_observation_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_forecast_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_cdf_forecast_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_site TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_observation TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_forecast TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_cdf_forecasts_single TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_cdf_forecasts_group TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_observation_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_forecast_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_cdf_forecast_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_site TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_observation TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_forecast TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_cdf_forecasts_single TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_cdf_forecasts_group TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_site TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_observation TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_forecast TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_cdf_forecasts_group TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_cdf_forecasts_single TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_sites TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_observations TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_forecasts TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_cdf_forecasts_groups TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_cdf_forecasts_singles TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_reports TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_report TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_report_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_report TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_report_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_report_metrics TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_report_status TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_report TO 'apiuser'@'%';


-- User/ Role / Permissions procedures
GRANT EXECUTE ON PROCEDURE arbiter_data.read_user TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_users TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_role_to_user TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_role_from_user TO 'apiuser'@'%';


GRANT EXECUTE ON PROCEDURE arbiter_data.create_role TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_role TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_roles TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_role TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_permission_from_role TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_permission_to_role TO 'apiuser'@'%';

GRANT EXECUTE ON PROCEDURE arbiter_data.list_permissions TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_permission TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_permission TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_permission TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_object_to_permission TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_object_from_permission TO 'apiuser'@'%';

