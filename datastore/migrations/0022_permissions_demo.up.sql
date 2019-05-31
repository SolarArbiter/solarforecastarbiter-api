/* Create orgs, users and an organization role */
-- Forecaster A setup
SET @fxaorgid = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.organizations (name, id, accepted_tou) VALUES (
    'Forecast Provider A', @fxaorgid, TRUE);

SET @fxaid = (SELECT UUID_TO_BIN('4b436bee-8245-11e9-a81f-54bf64606445', 1));
insert into arbiter_data.users (id, auth0_id, organization_id) values (
    @fxaid, 'auth0|5ceed7c8a1536b1103699501', @fxaorgid);


-- Forecaster B setup
SET @fxborgid = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.organizations (name, id, accepted_tou) VALUES (
    'Forecast Provider B', @fxborgid, TRUE);

SET @fxbid = (SELECT UUID_TO_BIN('6b230ff0-8245-11e9-a81f-54bf64606445',1));
insert into arbiter_data.users (id, auth0_id, organization_id) values (
    @fxbid, 'auth0|5ceed7ee160e0810f79b5223', @fxborgid);

-- Utility  setup
SET @utilxorgid = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.organizations (name, id, accepted_tou) VALUES (
    'Utility X', @utilxorgid, TRUE);
SET @utilxid = (SELECT UUID_TO_BIN('7475a52c-8245-11e9-a81f-54bf64606445',1));
insert into arbiter_data.users (id, auth0_id, organization_id) values (
    @utilxid, 'auth0|5ceed81307926110fccc7319', @utilxorgid);


-- Create a Power plant for Utilitty X 
SET @plant_id = (UUID_TO_BIN('c3f01422-824d-11e9-a81f-54bf64606445', 1));
INSERT INTO arbiter_data.sites (
    id, organization_id, name, latitude, longitude, elevation, timezone, extra_parameters,
    ac_capacity, dc_capacity, temperature_coefficient, tracking_type, surface_tilt, surface_azimuth,
    ac_loss_factor, dc_loss_factor, created_at, modified_at
) VALUES (
    @plant_id, 
    @utilxorgid, 
    'Power Plant X', 43.73403, -96.62328, 786.0, 'Etc/GMT+6', '', 10.0, 12.0, 
    -0.002, 'fixed', 45.0, 180, 0, 0, 
    TIMESTAMP('2019-05-29 11:44:46'), TIMESTAMP('2019-05-29 11:44:46') 
);

-- Create observations at plant x for the utility 
INSERT INTO arbiter_data.observations (
    id, organization_id, site_id, name, variable, interval_label,  interval_length, interval_value_type,
    uncertainty, extra_parameters, created_at, modified_at
) VALUES (
    UUID_TO_BIN('825fa193-824f-11e9-a81f-54bf64606445', 1),
    @utilxorgid,
    UUID_TO_BIN('c3f01422-824d-11e9-a81f-54bf64606445', 1),
    'GHI Instrument 1', 'ghi', 'beginning', 5, 'interval_mean', 0.10, '',
    TIMESTAMP('2019-03-01 12:01:39'), TIMESTAMP('2019-03-01 12:01:39')
), (
    UUID_TO_BIN('825fa192-824f-11e9-a81f-54bf64606445', 1),
    @utilxorgid,
    UUID_TO_BIN('c3f01422-824d-11e9-a81f-54bf64606445', 1),
    'DHI instrument 1', 'dhi', 'beginning', 5, 'interval_mean', 0.10,'',
    TIMESTAMP('2019-03-01 12:01:43'), TIMESTAMP('2019-03-01 12:01:43')
), (
    UUID_TO_BIN('95890740-824f-11e9-a81f-54bf64606445', 1),
    @utilxorgid,
    UUID_TO_BIN('c3f01422-824d-11e9-a81f-54bf64606445', 1),
    'DNI', 'dni', 'beginning', 5, 'interval_mean', 0.10, '',
    TIMESTAMP('2019-03-01 12:01:48'), TIMESTAMP('2019-03-01 12:01:48')
), (
    UUID_TO_BIN('47ebb068-8250-11e9-a81f-54bf64606445', 1),
    @utilxorgid,
    UUID_TO_BIN('c3f01422-824d-11e9-a81f-54bf64606445', 1),
    'AC Power', 'ac_power', 'beginning', 5, 'interval_mean', 0.05, '',
    TIMESTAMP('2019-03-01 11:55:38'), TIMESTAMP('2019-03-01 11:55:38')
);
-- Create a role to allow forecasters to read the site and observations
SET @utilx_read_role = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES (
    'Read Plant X', 'Read metadata for the site and observations for producing forecasts.', @utilx_read_role, @utilxorgid);

SET @read_plant_obs = (SELECT UUID_TO_BIN(UUID(), 1));
SET @read_plant_values = (SELECT UUID_TO_BIN(UUID(), 1));
SET @read_plant_meta = (SELECT UUID_TO_BIN(UUID(), 1));
SET @read_plant_roles = (SELECT UUID_TO_BIN(UUID(), 1));
SET @read_plant_perms = (SELECT UUID_TO_BIN(UUID(), 1));

INSERT INTO arbiter_data.permissions(id, description, organization_id, action, object_type, applies_to_all) VALUES (
    @read_plant_obs, 'Read Plant X observation metadata', @utilxorgid, 'read', 'observations', FALSE), (
    @read_plant_values, 'Read Plant X observation values', @utilxorgid, 'read_values', 'observations', FALSE), (
    @read_plant_meta, 'Read Plant X site metadata', @utilxorgid, 'read', 'sites', FALSE), (
    @read_plant_roles, 'View plant x roles', @utilxorgid, 'read', 'roles', FALSE), (
    @read_plant_perms, 'View plant x permissions', @utilxorgid, 'read', 'permissions', FALSE); 

INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @read_plant_obs, id FROM arbiter_data.observations WHERE site_id = @plant_id AND organization_id = @utilxorgid;
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @read_plant_values, id FROM arbiter_data.observations WHERE site_id = @plant_id AND organization_id = @utilxorgid;
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @read_plant_roles, id FROM arbiter_data.roles WHERE organization_id = @utilxorgid;
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @read_plant_perms, id FROM arbiter_data.permissions WHERE organization_id = @utilxorgid;
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) VALUES(
    @read_plant_meta, @plant_id);
INSERT INTO arbiter_data.role_permission_mapping(role_id, permission_id) SELECT @utilx_read_role, id from arbiter_data.permissions where organization_id = @utilxorgid;

INSERT INTO arbiter_data.user_role_mapping(user_id, role_id) VALUES (
    @fxaid, @utilx_read_role), (
    @fxbid, @utilx_read_role);

-- create forecasts at plant x for Forecaster A 
INSERT INTO arbiter_data.forecasts (
    id, organization_id, site_id, name, variable, issue_time_of_day, lead_time_to_start,
    interval_label, interval_length, run_length, interval_value_type, extra_parameters,
    created_at, modified_at
) VALUES (
    UUID_TO_BIN('e7ab1710-8250-11e9-a81f-54bf64606445', 1),
    @fxaorgid,
    UUID_TO_BIN('c3f01422-824d-11e9-a81f-54bf64606445', 1),
    'HA Power', 'ac_power', '12:00', 60, 'beginning', 1, 60, 'interval_mean', '',
    TIMESTAMP('2019-03-01 11:55:38'), TIMESTAMP('2019-03-01 11:55:38')
);

-- create a role to read the forecast from Forecaster A
SET @fxa_read_role = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES (
    'Read Forecaster A Plant x Forecast', 'Read forecaster a metadata and forecat values for Plant X', @fxa_read_role, @fxaorgid);

SET @fxa_read_meta_perm = (SELECT UUID_TO_BIN(UUID(), 1));
SET @fxa_read_values_perm =(SELECT UUID_TO_BIN(UUID(), 1));
SET @read_fxa_role = (SELECT UUID_TO_BIN(UUID(), 1));
SET @read_fxa_role_perms = (SELECT UUID_TO_BIN(UUID(), 1));

INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
    @fxa_read_meta_perm, 'Read Forecaster A plant x forecast metadata', @fxaorgid, 'read', 'forecasts', FALSE), (
    @fxa_read_values_perm, 'Read Forecaster A plant x forecast values', @fxaorgid, 'read_values', 'forecasts', FALSE),(
    @read_fxa_role, 'Read Forecaster A plant role', @fxaorgid, 'read', 'roles', FALSE), (
    @read_fxa_role_perms, 'Read Forecaster A Plant permissions', @fxaorgid, 'read', 'permissions', FALSE);

INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @fxa_read_meta_perm, id FROM arbiter_data.forecasts WHERE organization_id = @fxaorgid;
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @fxa_read_values_perm,  id FROM arbiter_data.forecasts WHERE organization_id = @fxaorgid;
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @read_fxa_role_perms, id FROM arbiter_data.permissions WHERE organization_id = @fxaorgid;
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) VALUES (@read_fxa_role, @fxa_read_role);
INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) SELECT @fxa_read_role, id FROM arbiter_data.permissions WHERE organization_id = @fxaorgid;

INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (@utilxid, @fxa_read_role);


--  Create forecasts at plant x fore Forecaster B 
INSERT INTO arbiter_data.forecasts (
    id, organization_id, site_id, name, variable, issue_time_of_day, lead_time_to_start,
    interval_label, interval_length, run_length, interval_value_type, extra_parameters,
    created_at, modified_at
) VALUES (
    UUID_TO_BIN('34bf6f4d-8251-11e9-a81f-54bf64606445', 1),
    @fxborgid,
    UUID_TO_BIN('c3f01422-824d-11e9-a81f-54bf64606445', 1),
    'HA Power', 'ac_power', '12:00', 60, 'beginning', 1, 60, 'interval_mean', '',
    TIMESTAMP('2019-03-01 11:55:38'), TIMESTAMP('2019-03-01 11:55:38')
);


-- create a role to read the forecast from Forecaster B
SET @fxb_read_role = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES (
    'Read Forecaster B Plant x Forecast', 'Read forecaster B metadata and forecat values for Plant X', @fxb_read_role, @fxborgid);

SET @fxb_read_meta_perm = (SELECT UUID_TO_BIN(UUID(), 1));
SET @fxb_read_values_perm =(SELECT UUID_TO_BIN(UUID(), 1));
SET @read_fxb_role = (SELECT UUID_TO_BIN(UUID(), 1));
SET @read_fxb_role_perms = (SELECT UUID_TO_BIN(UUID(), 1));

INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
    @fxb_read_meta_perm, 'Read Forecaster B plant x forecast metadata', @fxborgid, 'read', 'forecasts', FALSE), (
    @fxb_read_values_perm, 'Read Forecaster B plant x forecast values', @fxborgid, 'read_values', 'forecasts', FALSE),(
    @read_fxb_role, 'Read Forecaster B plant role', @fxborgid, 'read', 'roles', false), (
    @read_fxb_role_perms, 'Read Forecaster B Plant permissions', @fxborgid, 'read', 'permissions', FALSE);
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @fxb_read_meta_perm, id FROM arbiter_data.forecasts WHERE organization_id = @fxborgid;
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @fxb_read_values_perm,  id FROM arbiter_data.forecasts WHERE organization_id = @fxborgid;
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @read_fxb_role_perms, id FROM arbiter_data.permissions WHERE organization_id = @fxborgid;
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) VALUES (@read_fxb_role, @fxb_read_role);
INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) SELECT @fxb_read_role, id FROM arbiter_data.permissions WHERE organization_id = @fxborgid;

INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (@utilxid, @fxb_read_role);


-- Create forecasts at the Weather Station site that other users can't see
INSERT INTO arbiter_data.forecasts (
    id, organization_id, site_id, name, variable, issue_time_of_day, lead_time_to_start,
    interval_label, interval_length, run_length, interval_value_type, extra_parameters,
    created_at, modified_at
) VALUES (
    UUID_TO_BIN('d0dd64fc-8250-11e9-a81f-54bf64606445', 1),
    @fxaorgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    'DA GHI', 'ghi', '06:00', 60, 'beginning', 5, 1440, 'interval_mean', '',
    TIMESTAMP('2019-03-01 11:55:37'), TIMESTAMP('2019-03-01 11:55:37')
), (
    UUID_TO_BIN('34bf6f4c-8251-11e9-a81f-54bf64606445', 1),
    @fxborgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    'DA GHI', 'ghi', '06:00', 60, 'beginning', 5, 1440, 'interval_mean', '',
    TIMESTAMP('2019-03-01 11:55:37'), TIMESTAMP('2019-03-01 11:55:37')
);

-- Allow each user all priveleges in their organizaiton
-- Forecaster A
SET @fxa_org_role = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES (
    'Forecaster A', 'Forecaster A full organization access', @fxa_org_role, @fxaorgid); 

INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (@fxaid, @fxa_org_role); 
INSERT INTO arbiter_data.permissions(description, organization_id, action, object_type, applies_to_all) VALUES(
    'Read all sites', @fxaorgid, 'read', 'sites', TRUE), (
    'Read all forecasts', @fxaorgid, 'read', 'forecasts', TRUE), (
    'Read all cdf forecasts', @fxaorgid, 'read', 'cdf_forecasts', TRUE), (
    'Read all observations', @fxaorgid, 'read', 'observations', TRUE), (
    'Read all forecast values', @fxaorgid, 'read_values', 'forecasts', TRUE), (
    'Read all cdf forecast values', @fxaorgid, 'read_values', 'cdf_forecasts', TRUE), (
    'Read all observation values', @fxaorgid, 'read_values', 'observations', TRUE), (
    'Create all sites', @fxaorgid, 'create', 'sites', TRUE), (
    'Create all forecasts', @fxaorgid, 'create', 'forecasts', TRUE), (
    'Create all cdf forecasts', @fxaorgid, 'create', 'cdf_forecasts', TRUE), (
    'Create all observations', @fxaorgid, 'create', 'observations', TRUE), (
    'Delete all sites', @fxaorgid, 'delete', 'sites', TRUE), (
    'Delete all forecasts', @fxaorgid, 'delete', 'forecasts', TRUE), (
    'Delete all cdf forecasts', @fxaorgid, 'delete', 'cdf_forecasts', TRUE), (
    'Delete all observations', @fxaorgid, 'delete', 'observations', TRUE), (
    'Delete all forecast values', @fxaorgid, 'delete_values', 'forecasts', TRUE), (
    'Delete all cdf forecast values', @fxaorgid, 'delete_values', 'cdf_forecasts', TRUE), (
    'Delete all observation values', @fxaorgid, 'delete_values', 'observations', TRUE), (
    'Write forecast values', @fxaorgid, 'write_values', 'forecasts', TRUE), (
    'Write cdf forecast values', @fxaorgid, 'write_values', 'cdf_forecasts', TRUE), (
    'Write observation values', @fxaorgid, 'write_values', 'observations', TRUE), (
    'Update Cdf Group', @fxaorgid, 'update', 'cdf_forecasts', TRUE), (
    'Read all users', @fxaorgid, 'read', 'users', TRUE), (
    'Read all roles', @fxaorgid, 'read', 'roles', TRUE), (
    'Read all permissions', @fxaorgid, 'read', 'permissions', TRUE);
INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) SELECT @fxa_org_role, id from arbiter_data.permissions WHERE organization_id = @fxaorgid;

-- Forecaster B
SET @fxb_org_role = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES (
    'Forecaster B', 'Forecaster B full organization access', @fxb_org_role, @fxborgid);

INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (@fxbid, @fxb_org_role);
INSERT INTO arbiter_data.permissions(description, organization_id, action, object_type, applies_to_all) VALUES(
    'Read all sites', @fxborgid, 'read', 'sites', TRUE), (
    'Read all forecasts', @fxborgid, 'read', 'forecasts', TRUE), (
    'Read all cdf forecasts', @fxborgid, 'read', 'cdf_forecasts', TRUE), (
    'Read all observations', @fxborgid, 'read', 'observations', TRUE), (
    'Read all forecast values', @fxborgid, 'read_values', 'forecasts', TRUE), (
    'Read all cdf forecast values', @fxborgid, 'read_values', 'cdf_forecasts', TRUE), (
    'Read all observation values', @fxborgid, 'read_values', 'observations', TRUE), (
    'Create all sites', @fxborgid, 'create', 'sites', TRUE), (
    'Create all forecasts', @fxborgid, 'create', 'forecasts', TRUE), (
    'Create all cdf forecasts', @fxborgid, 'create', 'cdf_forecasts', TRUE), (
    'Create all observations', @fxborgid, 'create', 'observations', TRUE), (
    'Delete all sites', @fxborgid, 'delete', 'sites', TRUE), (
    'Delete all forecasts', @fxborgid, 'delete', 'forecasts', TRUE), (
    'Delete all cdf forecasts', @fxborgid, 'delete', 'cdf_forecasts', TRUE), (
    'Delete all observations', @fxborgid, 'delete', 'observations', TRUE), (
    'Delete all forecast values', @fxborgid, 'delete_values', 'forecasts', TRUE), (
    'Delete all cdf forecast values', @fxborgid, 'delete_values', 'cdf_forecasts', TRUE), (
    'Delete all observation values', @fxborgid, 'delete_values', 'observations', TRUE), (
    'Write forecast values', @fxborgid, 'write_values', 'forecasts', TRUE), (
    'Write cdf forecast values', @fxborgid, 'write_values', 'cdf_forecasts', TRUE), (
    'Write observation values', @fxborgid, 'write_values', 'observations', TRUE), (
    'Update Cdf Group', @fxborgid, 'update', 'cdf_forecasts', TRUE), (
    'Read all users', @fxborgid, 'read', 'users', TRUE), (
    'Read all roles', @fxborgid, 'read', 'roles', TRUE), (
    'Read all permissions', @fxborgid, 'read', 'permissions', TRUE);

INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) SELECT @fxb_org_role, id from arbiter_data.permissions WHERE organization_id = @fxborgid;

-- Utility 
SET @utilx_org_role = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES (
    'Utility X', 'Utility X full organization access', @utilx_org_role, @utilxorgid);

INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (@utilxid, @utilx_org_role); 
INSERT INTO arbiter_data.permissions(description, organization_id, action, object_type, applies_to_all) VALUES(
    'Read all sites', @utilxorgid, 'read', 'sites', TRUE), (
    'Read all forecasts', @utilxorgid, 'read', 'forecasts', TRUE), (
    'Read all cdf forecasts', @utilxorgid, 'read', 'cdf_forecasts', TRUE), (
    'Read all observations', @utilxorgid, 'read', 'observations', TRUE), (
    'Read all forecast values', @utilxorgid, 'read_values', 'forecasts', TRUE), (
    'Read all cdf forecast values', @utilxorgid, 'read_values', 'cdf_forecasts', TRUE), (
    'Read all observation values', @utilxorgid, 'read_values', 'observations', TRUE), (
    'Create all sites', @utilxorgid, 'create', 'sites', TRUE), (
    'Create all forecasts', @utilxorgid, 'create', 'forecasts', TRUE), (
    'Create all cdf forecasts', @utilxorgid, 'create', 'cdf_forecasts', TRUE), (
    'Create all observations', @utilxorgid, 'create', 'observations', TRUE), (
    'Delete all sites', @utilxorgid, 'delete', 'sites', TRUE), (
    'Delete all forecasts', @utilxorgid, 'delete', 'forecasts', TRUE), (
    'Delete all cdf forecasts', @utilxorgid, 'delete', 'cdf_forecasts', TRUE), (
    'Delete all observations', @utilxorgid, 'delete', 'observations', TRUE), (
    'Delete all forecast values', @utilxorgid, 'delete_values', 'forecasts', TRUE), (
    'Delete all cdf forecast values', @utilxorgid, 'delete_values', 'cdf_forecasts', TRUE), (
    'Delete all observation values', @utilxorgid, 'delete_values', 'observations', TRUE), (
    'Write forecast values', @utilxorgid, 'write_values', 'forecasts', TRUE), (
    'Write cdf forecast values', @utilxorgid, 'write_values', 'cdf_forecasts', TRUE), (
    'Write observation values', @utilxorgid, 'write_values', 'observations', TRUE), (
    'Update Cdf Group', @utilxorgid, 'update', 'cdf_forecasts', TRUE), (
    'Read all users', @utilxorgid, 'read', 'users', TRUE), (
    'Read all roles', @utilxorgid, 'read', 'roles', TRUE), (
    'Read all permissions', @utilxorgid, 'read', 'permissions', TRUE);
INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) SELECT @utilx_org_role, id from arbiter_data.permissions WHERE organization_id = @utilxorgid;


SET @weather_station_role = (SELECT UUID_TO_BIN(UUID(), 1));
SET @orgid = (SELECT UUID_TO_BIN('b76ab62e-4fe1-11e9-9e44-64006a511e6f', 1));
SET @weather_station_id = (SELECT UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1));
SET @read_weather_station = (SELECT UUID_TO_BIN(UUID(), 1));
SET @read_weather_station_obs = (SELECT UUID_TO_BIN(UUID(), 1));
SET @read_weather_station_obs_values = (SELECT UUID_TO_BIN(UUID(), 1));

INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES (
    'Read Weather Station', 'Allows User to read Site and Observation data', @weather_station_role, @orgid);
INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
    @read_weather_station, 'Read Ashland OR Site', @orgid, 'read', 'sites', FALSE), (
    @read_weather_station_obs, 'Read Ashland OR Observations', @orgid, 'read', 'observations', FALSE), (
    @read_weather_station_obs_values, 'Read Ashland OR Observation values', @orgid, 'read_values', 'observations', FALSE);

INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) VALUES (
    @read_weather_station, @weather_station_id); 
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @read_weather_station_obs, id FROM arbiter_data.observations WHERE site_id = @weather_station_id;
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id) SELECT @read_weather_station_obs_Values, id FROM arbiter_data.observations WHERE site_id = @weather_station_id;
INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (
    @weather_station_role, @read_weather_station), (
    @weather_station_role, @read_weather_station_obs), (
    @weather_station_role, @read_weather_station_obs_values);
  
INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (
    @fxaid, @weather_station_role), (
    @fxbid, @weather_station_role), (
    @utilxid, @weather_station_role);

SET @reference_reader = (SELECT id FROM arbiter_data.roles where name = 'Read Reference Data');
-- Add read reference data to everyone
INSERT INTO arbiter_data.user_role_mapping(user_id, role_id) VALUES(
    @utilxid, @reference_reader), (
    @fxaid, @reference_reader), (
    @fxbid, @reference_reader);
