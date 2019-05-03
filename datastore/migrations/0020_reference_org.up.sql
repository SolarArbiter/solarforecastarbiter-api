SET @orgid = UUID_TO_BIN(UUID(), 1);

SET @userid = (SELECT id FROM arbiter_data.users WHERE auth0_id = 'auth0|5be343df7025406237820b85');

INSERT INTO arbiter_data.organizations (name, id, accepted_tou) VALUES (
    'Reference', @orgid, TRUE);

SET @reference_userid = UUID_TO_BIN(UUID(), 1);

INSERT INTO arbiter_data.users (id, auth0_id, organization_id) VALUES (
    @reference_userid, 'auth0|5cc8aeff0ec8b510a4c7f2f1', @orgid);

SET @roleid = UUID_TO_BIN(UUID(), 1);

INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES(
    'Read Reference Data',
    'Role to read reference sites, forecasts, and observations',
    @roleid, @orgid);

INSERT INTO arbiter_data.permissions (description, organization_id, action, object_type, applies_to_all) VALUES (
    'Read all sites', @orgid, 'read', 'sites', TRUE), (
    'Read all forecasts', @orgid, 'read', 'forecasts', TRUE), (
    'Read all forecast values', @orgid, 'read_values', 'forecasts', TRUE), (
    'Read all CDF forecasts', @orgid, 'read', 'cdf_forecasts', TRUE), (
    'Read all CDF forecast values', @orgid, 'read_values', 'cdf_forecasts', TRUE), (
    'Read all observations', @orgid, 'read', 'observations', TRUE), (
    'Read all observation values', @orgid, 'read_values', 'observations', TRUE);

INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) SELECT @roleid, id FROM arbiter_data.permissions WHERE organization_id = @orgid;

SET @reference_roleid = UUID_TO_BIN(UUID(), 1);

INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES(
    'Reference user role',
    'Role to read and create all reference data.',
    @reference_roleid, @orgid);

INSERT INTO arbiter_data.permissions (description, organization_id, action, object_type, applies_to_all) VALUES (
    'Create all sites', @orgid, 'create', 'sites', TRUE), (
    'Delete all sites', @orgid, 'delete', 'sites', TRUE), (
    'Create all forecasts', @orgid, 'create', 'forecasts', TRUE), (
    'Delete all forecasts', @orgid, 'delete', 'forecasts', TRUE), (
    'Create all forecast values', @orgid, 'write_values', 'forecasts', TRUE), (
    'Delete all forecast values', @orgid, 'delete_values', 'forecasts', TRUE), (
    'Create all CDF forecasts', @orgid, 'create', 'cdf_forecasts', TRUE), (
    'Delete all CDF forecasts', @orgid, 'delete', 'cdf_forecasts', TRUE), (
    'Create all CDF forecast values', @orgid, 'write_values', 'cdf_forecasts', TRUE), (
    'Delete all CDF forecast values', @orgid, 'delete_values', 'cdf_forecasts', TRUE), (
    'Create all observations', @orgid, 'create', 'observations', TRUE), (
    'Delete all observations', @orgid, 'delete', 'observations', TRUE), (
    'Create all observation values', @orgid, 'write_values', 'observations', TRUE), (
    'Delete all observation values', @orgid, 'delete_values', 'observations', TRUE);


INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) SELECT @reference_roleid, id FROM arbiter_data.permissions WHERE organization_id = @orgid;

INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (@userid, @roleid);
INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (@reference_userid, @reference_roleid);


SET @siteid = UUID_TO_BIN(UUID(), 1);
INSERT INTO arbiter_data.sites (
    id, organization_id, name, latitude, longitude, elevation, timezone,
    extra_parameters,  ac_capacity, dc_capacity, temperature_coefficient,
    tracking_type, surface_tilt, surface_azimuth,
    ac_loss_factor, dc_loss_factor
) VALUES (
    @siteid, @orgid, 'PSEL Reference System', 35.05, -106.54, 1657.0,
    'America/Denver', '{"network": "Sandia RTC"}', 0.003, 0.003, -0.004,
    'fixed', 35.0, 180.0, 0, 0
);


INSERT INTO arbiter_data.forecasts (
    organization_id, site_id, name, variable, issue_time_of_day,
    lead_time_to_start, interval_label, interval_length, run_length,
    interval_value_type, extra_parameters
) VALUES (
    @orgid, @siteid, 'Next day as of noon PSEL Reference POA Irradiance',
    'poa_global', '00:00', 720, 'beginning', 5, 1440, 'interval_mean',
    '{"network": "Sandia RTC"}'), (
    @orgid, @siteid, 'Next day as of noon PSEL Reference AC Power',
    'ac_power', '00:00', 720, 'beginning', 5, 1440, 'interval_mean',
    '{"network": "Sandia RTC"}'), (
    @orgid, @siteid, 'Next day as of noon PSEL Reference DC Power',
    'dc_power', '00:00', 720, 'beginning', 5, 1440, 'interval_mean',
    '{"network": "Sandia RTC"}'
);


INSERT INTO arbiter_data.observations (
    organization_id, site_id, name, variable, interval_label, interval_length,
    interval_value_type, uncertainty, extra_parameters
) VALUES (
    @orgid, @siteid, 'PSEL Reference POA Irradiance', 'poa_global', 'beginning',
    1, 'instantaneous', 0.10, '{"network": "Sandia RTC"}'), (
    @orgid, @siteid, 'PSEL Reference Air Temperature', 'air_temperature', 'beginning',
    1, 'instantaneous', 0.10, '{"network": "Sandia RTC"}'), (
    @orgid, @siteid, 'PSEL Reference Sys 1 AC Power', 'ac_power', 'beginning',
    1, 'instantaneous', 0.10, '{"network": "Sandia RTC"}'), (
    @orgid, @siteid, 'PSEL Reference Sys 1 DC Power', 'dc_power', 'beginning',
    1, 'instantaneous', 0.10, '{"network": "Sandia RTC"}'), (
    @orgid, @siteid, 'PSEL Reference Sys 2 AC Power', 'ac_power', 'beginning',
    1, 'instantaneous', 0.10, '{"network": "Sandia RTC"}'), (
    @orgid, @siteid, 'PSEL Reference Sys 2 DC Power', 'dc_power', 'beginning',
    1, 'instantaneous', 0.10, '{"network": "Sandia RTC"}'
);
