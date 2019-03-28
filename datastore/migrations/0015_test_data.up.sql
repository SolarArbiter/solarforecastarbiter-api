SET @orgid = (SELECT UUID_TO_BIN('b76ab62e-4fe1-11e9-9e44-64006a511e6f', 1));

INSERT INTO arbiter_data.organizations (name, id, accepted_tou) VALUES (
    'Reference', @orgid, TRUE);

SET @userid = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.users (id, auth0_id, organization_id) VALUES (
    @userid, 'auth0|testtesttest', @orgid);

SET @roleid = (SELECT UUID_TO_BIN(UUID(), 1));
INSERT INTO arbiter_data.roles (name, description, id, organization_id) VALUES (
    'Test user role', 'Role for the test user to read, create, delete test objects',
    @roleid, @orgid);

INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (@userid, @roleid);

INSERT INTO arbiter_data.sites (
    id, organization_id, name, latitude, longitude, elevation, timezone, extra_parameters
) VALUES (
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    @orgid,
    'Ashland OR', 42.19, -122.7, 595.0, 'Etc/GMT+8',
    '{"network_api_abbreviation": "AS","network": "University of Oregon SRML","network_api_id": "94040"}'
), (
    UUID_TO_BIN('d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a', 1),
    @orgid,
    'Weather Station 1', 32.22969, -110.95534, 786.0, 'America/Phoenix', '{"network": "NREL MIDC"}'
);


INSERT INTO arbiter_data.permissions (description, organization_id, action, object_type, applies_to_all) VALUES (
    'Read all sites', @orgid, 'read', 'sites', TRUE), (
    'Read all forecasts', @orgid, 'read', 'forecasts', TRUE), (
    'Read all observations', @orgid, 'read', 'observations', TRUE), (
    'Read all forecast values', @orgid, 'read_values', 'forecasts', TRUE), (
    'Read all observation values', @orgid, 'read_values', 'observations', TRUE), (
    'Create all sites', @orgid, 'create', 'sites', TRUE), (
    'Create all forecasts', @orgid, 'create', 'forecasts', TRUE), (
    'Create all observations', @orgid, 'create', 'observations', TRUE), (
    'Delete all sites', @orgid, 'delete', 'sites', TRUE), (
    'Delete all forecasts', @orgid, 'delete', 'forecasts', TRUE), (
    'Delete all observations', @orgid, 'delete', 'observations', TRUE), (
    'Delete all forecast values', @orgid, 'delete_values', 'forecasts', TRUE), (
    'Delete all observation values', @orgid, 'delete_values', 'observations', TRUE), (
    'Write forecast values', @orgid, 'write_values', 'forecasts', TRUE), (
    'Write observation values', @orgid, 'write_values', 'observations', TRUE);

INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) SELECT @roleid, id FROM arbiter_data.permissions WHERE organization_id = @orgid;


INSERT INTO arbiter_data.sites (
    id, organization_id, name, latitude, longitude, elevation, timezone, extra_parameters,
    ac_capacity, dc_capacity, temperature_coefficient, tracking_type, surface_tilt, surface_azimuth,
    ac_loss_factor, dc_loss_factor
) VALUES (
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440002', 1),
    @orgid,
    'Power Plant 1', 43.73403, -96.62328, 786.0, 'Etc/GMT+6', '', 0.015, 0.015,
    -0.002, 'fixed', 45.0, 180, 0, 0
);


INSERT INTO arbiter_data.forecasts (
    id, organization_id, site_id, name, variable, issue_time_of_day, lead_time_to_start,
    interval_label, interval_length, run_length, interval_value_type, extra_parameters
) VALUES (
    UUID_TO_BIN('11c20780-76ae-4b11-bef1-7a75bdc784e3', 1),
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    'DA Power', 'ac_power', '06:00', 60, 'beginning', 5, 1440, 'interval_mean', ''
), (
    UUID_TO_BIN('f8dd49fa-23e2-48a0-862b-ba0af6dec276', 1),
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440002', 1),
    'HA Power', 'ac_power', '12:00', 60, 'beginning', 1, 60, 'interval_mean', ''
);


INSERT INTO arbiter_data.observations (
    id, organization_id, site_id, name, variable, interval_label,  interval_length, interval_value_type,
    uncertainty, extra_parameters
) VALUES (
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440000', 1),
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    'GHI Instrument 1', 'ghi', 'beginning', 5, 'interval_mean', 0.10,
    '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer"}'
), (
    UUID_TO_BIN('9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f', 1),
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    'DHI Instrument 1', 'dhi', 'beginning', 5, 'interval_mean', 0.10,
    '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer"}'
), (
    UUID_TO_BIN('9ce9715c-bd91-47b7-989f-50bb558f1eb9', 1),
    @orgid,
    UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1),
    'DNI Instrument 1', 'dni', 'beginning', 5, 'interval_mean', 0.10,
    '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer"}'
), (
    UUID_TO_BIN('e0da0dea-9482-4073-84de-f1b12c304d23', 1),
    @orgid,
    UUID_TO_BIN('d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a', 1),
    'GHI Instrument 2', 'ghi', 'beginning', 5, 'interval_mean', 0.10,
    '{"instrument": "Kipp & Zonen CMP 22 Pyranometer"}'
), (
    UUID_TO_BIN('b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2', 1),
    @orgid,
    UUID_TO_BIN('d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a', 1),
    'Sioux Falls, ghi', 'ghi', 'beginning', 5, 'interval_mean', 0.10,
    '{"instrument": "Kipp & Zonen CMP 22 Pyranometer"}'
);


CREATE PROCEDURE insertfx(IN fxid CHAR(36))
BEGIN
    SET @id = (SELECT UUID_TO_BIN(fxid, 1));
    SET @timestamp = TIMESTAMP('2019-01-01 12:00');
    REPEAT
        INSERT INTO arbiter_data.forecasts_values (id, timestamp, value) VALUES (@id, @timestamp, RAND());
        SET @timestamp = (SELECT TIMESTAMPADD(MINUTE, 1, @timestamp));
    UNTIL @timestamp = TIMESTAMP('2019-01-01 12:20') END REPEAT;
END;

CREATE PROCEDURE insertobs(IN obsid CHAR(36))
BEGIN
    SET @id = (SELECT UUID_TO_BIN(obsid, 1));
    SET @timestamp = TIMESTAMP('2019-01-01 12:00');
    REPEAT
        INSERT INTO arbiter_data.observations_values (id, timestamp, value, quality_flag) VALUES (
            @id, @timestamp, RAND(), 0);
        SET @timestamp = (SELECT TIMESTAMPADD(MINUTE, 1, @timestamp));
    UNTIL @timestamp = TIMESTAMP('2019-01-01 12:20') END REPEAT;
END;

CALL insertfx('11c20780-76ae-4b11-bef1-7a75bdc784e3');
CALL insertfx('f8dd49fa-23e2-48a0-862b-ba0af6dec276');

CALL insertobs('123e4567-e89b-12d3-a456-426655440000');
CALL insertobs('9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f');
CALL insertobs('9ce9715c-bd91-47b7-989f-50bb558f1eb9');
CALL insertobs('e0da0dea-9482-4073-84de-f1b12c304d23');
CALL insertobs('b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2');


CREATE USER 'apiuser'@'%' IDENTIFIED BY 'thisisaterribleandpublicpassword';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_observation_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_forecast_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_site TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_observation TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_forecast TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_observation_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_forecast_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_site TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_observation TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_forecast TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_site TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_observation TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_forecast TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_sites TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_observations TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_forecasts TO 'apiuser'@'%';
