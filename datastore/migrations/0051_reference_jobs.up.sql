SET @reforgid = (SELECT id FROM organizations WHERE name = 'Reference');
SET @refauth0 = 'auth0|5cc8aeff0ec8b510a4c7f2f1';
SET @refid = (SELECT id FROM users WHERE auth0_id = @refauth0);
SET @baseurl = 'https://sfa-worker-api.development.svc';

SET @abqsite = UUID_TO_BIN(UUID(), 1);
SET @nvsite = UUID_TO_BIN(UUID(), 1);
SET @vtsite = UUID_TO_BIN(UUID(), 1);
SET @flsite = UUID_TO_BIN(UUID(), 1);

INSERT INTO sites (id, organization_id, name, latitude, longitude,
    elevation, timezone, extra_parameters, ac_capacity, dc_capacity,
    temperature_coefficient, tracking_type, surface_tilt,
    surface_azimuth, axis_tilt, axis_azimuth, ground_coverage_ratio,
    backtrack, max_rotation_angle, dc_loss_factor, ac_loss_factor )
VALUES (
    @abqsite, @reforgid, 'DOE RTC Albuquerque NM' , 35.050000 ,
    -106.530000 , 1657.00 , 'America/Denver' , '{"network": "DOE RTC",
    "network_api_id": "Albuquerque", "network_api_abbreviation": "",
    "observation_interval_length": 1, "attribution": "", "module":
    "Suniva 270W"}' , 0.003240 , 0.003240 , -0.00420 , 'fixed' , 35.00 ,
    180.00 , NULL , NULL , NULL , NULL , NULL , 0.00 , 0.00
),(
    @nvsite, @reforgid, 'DOE RTC Henderson NV' , 36.040000 , -114.920000 , 538.00 ,
    'America/Los_Angeles' , '{"network": "DOE RTC", "network_api_id":
    "Henderson", "network_api_abbreviation": "",
    "observation_interval_length": 1, "attribution": "", "module":
    "Suniva 270W"}' , 0.003240 , 0.003240 , -0.00420 , 'fixed' , 35.00 ,
    180.00 , NULL , NULL , NULL , NULL , NULL , 0.00 , 0.00
),(
    @vtsite, @reforgid, 'DOE RTC Williston VT' , 44.500000 , -73.100000 , 184.00 ,
    'America/New_York' , '{"network": "DOE RTC", "network_api_id":
    "Williston", "network_api_abbreviation": "",
    "observation_interval_length": 1, "attribution": "", "module":
    "Suniva 270W"}' , 0.003240 , 0.003240 , -0.00420 , 'fixed' , 35.00 ,
    180.00 , NULL , NULL , NULL , NULL , NULL , 0.00 , 0.00
),(
    @flsite, @reforgid, 'DOE RTC Cocoa FL' , 28.400000 , -80.770000 , 11.00 , 'America/New_York' ,
    '{"network": "DOE RTC", "network_api_id": "Cocoa",
    "network_api_abbreviation": "", "observation_interval_length": 1,
    "attribution": "", "module": "Suniva 270W"}' , 0.003240 , 0.003240
    , -0.00420 , 'fixed' , 35.00 , 180.00 , NULL , NULL , NULL , NULL ,
    NULL , 0.00 , 0.00
);

INSERT INTO forecasts (organization_id, site_id, name, variable, issue_time_of_day,
 lead_time_to_start, interval_label, interval_length, run_length,
 interval_value_type, extra_parameters
) VALUES(
 @reforgid, @abqsite, 'Albuquerque NM Day Ahead GFS ac_power' , 'ac_power' , '07:00' , 1440 , 'ending' , 60 ,
 1440 , 'interval_mean' , '{"is_reference_forecast": true, "model": "gfs_quarter_deg_hourly_to_hourly_mean"}'
),(@reforgid, @abqsite, 'Albuquerque NM Intraday HRRR ac_power', 'ac_power' , '00:00', 60 , 'ending' , 60 ,
 360 , 'interval_mean' , '{"is_reference_forecast": true, "model": "hrrr_subhourly_to_hourly_mean"}'
),(@reforgid, @abqsite, 'Albuquerque NM Intraday RAP ac_power', 'ac_power' , '00:00' , 60 , 'ending' , 60 , 360 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "rap_cloud_cover_to_hourly_mean"}'
),(@reforgid, @abqsite, 'Albuquerque NM Current Day NAM ac_power', 'ac_power' , '06:00' , 60 , 'ending' , 60 , 1440 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "nam_12km_cloud_cover_to_hourly_mean"}'
),(@reforgid, @nvsite, 'Henderson NV Day Ahead GFS ac_power', 'ac_power' , '08:00' , 1440 , 'ending' , 60 , 1440 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "gfs_quarter_deg_hourly_to_hourly_mean"}'
),(@reforgid, @nvsite, 'Henderson NV Intraday HRRR ac_power', 'ac_power' , '01:00' , 60 , 'ending' , 60 , 360 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "hrrr_subhourly_to_hourly_mean"}'
),(@reforgid, @nvsite, 'Henderson NV Intraday RAP ac_power', 'ac_power' , '01:00' , 60 , 'ending' , 60 , 360 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "rap_cloud_cover_to_hourly_mean"}'
),(@reforgid, @nvsite, 'Henderson NV Current Day NAM ac_power', 'ac_power' , '07:00' , 60 , 'ending' , 60 , 1440 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "nam_12km_cloud_cover_to_hourly_mean"}'
),(@reforgid, @vtsite, 'Williston VT Day Ahead GFS ac_power', 'ac_power' , '05:00' , 1440 , 'ending' , 60 , 1440 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "gfs_quarter_deg_hourly_to_hourly_mean"}'
),(@reforgid, @vtsite, 'Williston VT Intraday HRRR ac_power', 'ac_power' , '04:00' , 60 , 'ending' , 60 , 360 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "hrrr_subhourly_to_hourly_mean"}'
),(@reforgid, @vtsite, 'Williston VT Intraday RAP ac_power', 'ac_power' , '04:00' , 60 , 'ending' , 60 , 360 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "rap_cloud_cover_to_hourly_mean"}'
),(@reforgid, @vtsite, 'Williston VT Current Day NAM ac_power', 'ac_power' , '04:00' , 60 , 'ending' , 60 , 1440 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "nam_12km_cloud_cover_to_hourly_mean"}'
),(@reforgid, @flsite, 'Cocoa FL Day Ahead GFS ac_power', 'ac_power' , '05:00' , 1440 , 'ending' , 60 , 1440 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "gfs_quarter_deg_hourly_to_hourly_mean"}'
),(@reforgid, @flsite, 'Cocoa FL Intraday HRRR ac_power', 'ac_power' , '04:00' , 60 , 'ending' , 60 , 360 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "hrrr_subhourly_to_hourly_mean"}'
),(@reforgid, @flsite, 'Cocoa FL Intraday RAP ac_power' , 'ac_power' , '04:00' , 60 , 'ending' , 60 , 360 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "rap_cloud_cover_to_hourly_mean"}'
),(@reforgid, @flsite, 'Cocoa FL Current Day NAM ac_power', 'ac_power' , '04:00' , 60 , 'ending' , 60 , 1440 ,
 'interval_mean' , '{"is_reference_forecast": true, "model": "nam_12km_cloud_cover_to_hourly_mean"}'
);


SET @abqcg = UUID_TO_BIN(UUID(), 1);
SET @nvcg = UUID_TO_BIN(UUID(), 1);
SET @vtcg = UUID_TO_BIN(UUID(), 1);
SET @flcg = UUID_TO_BIN(UUID(), 1);
INSERT INTO cdf_forecasts_groups (id, site_id, organization_id, name, variable, issue_time_of_day, lead_time_to_start, interval_label, interval_length, run_length, interval_value_type, extra_parameters, axis
) VALUES (
  @abqcg, @abqsite, @reforgid, 'Albuquerque NM Day Ahead GEFS ac_power', 'ac_power', '07:00', 1440, 'ending', 60, 1440, 'interval_mean', '{"is_reference_forecast": true, "model": "gefs_half_deg_to_hourly_mean"}', 'y'), (
  @nvcg, @nvsite, @reforgid, 'Henderson NV Day Ahead GEFS ac_power', 'ac_power', '08:00', 1440, 'ending', 60, 1440, 'interval_mean', '{"is_reference_forecast": true, "model": "gefs_half_deg_to_hourly_mean"}', 'y'), (
  @vtcg, @vtsite, @reforgid, 'Williston VT Day Ahead GEFS ac_power', 'ac_power', '05:00', 1440, 'ending', 60, 1440, 'interval_mean', '{"is_reference_forecast": true, "model": "gefs_half_deg_to_hourly_mean"}', 'y'), (
  @flcg, @flsite, @reforgid, 'Cocoa FL Day Ahead GEFS ac_power', 'ac_power', '05:00', 1440, 'ending', 60, 1440, 'interval_mean', '{"is_reference_forecast": true, "model": "gefs_half_deg_to_hourly_mean"}', 'y'
);

CREATE PROCEDURE makecvs(IN gid BINARY(16))
BEGIN
   DECLARE cv float DEFAULT 0.0;

   WHILE cv < 101 DO
       INSERT INTO cdf_forecasts_singles (cdf_forecast_group_id, constant_value) VALUES (gid, cv);
       SET cv = cv + 5;
   END WHILE;
END;

CALL makecvs(@abqcg);
CALL makecvs(@nvcg);
CALL makecvs(@vtcg);
CALL makecvs(@flcg);


SET @abqobs = UUID_TO_BIN(UUID(), 1);
SET @nvobs = UUID_TO_BIN(UUID(), 1);
SET @vtobs = UUID_TO_BIN(UUID(), 1);
SET @flobs = UUID_TO_BIN(UUID(), 1);

INSERT INTO observations (id, organization_id, site_id, name, variable, interval_label, interval_length, interval_value_type, uncertainty, extra_parameters
) VALUES (
  @abqobs, @reforgid, @abqsite, 'Albuquerque NM ac_power', 'ac_power', 'ending', 1, 'interval_mean', 0, '{"network": "DOE RTC", "network_api_id": "Albuquerque", "network_api_abbreviation": "", "observation_interval_length": 1, "attribution": "", "module": "Suniva 270W"}'
), (
  @nvobs, @reforgid, @nvsite, 'Henderson NV ac_power', 'ac_power', 'ending', 1, 'interval_mean', 0, '{"network": "DOE RTC", "network_api_id": "Henderson", "network_api_abbreviation": "", "observation_interval_length": 1, "attribution": "", "module": "Suniva 270W"}'
), (
  @vtobs, @reforgid, @vtsite, 'Williston VT ac_power', 'ac_power', 'ending', 1, 'interval_mean', 0, '{"network": "DOE RTC", "network_api_id": "Williston", "network_api_abbreviation": "", "observation_interval_length": 1, "attribution": "", "module": "Suniva 270W"}'
), (
  @flobs, @reforgid, @flsite, 'Cocoa FL ac_power', 'ac_power', 'ending', 1, 'interval_mean', 0, '{"network": "DOE RTC", "network_api_id": "Cocoa", "network_api_abbreviation": "", "observation_interval_length": 1, "attribution": "", "module": "Suniva 270W"}'
);

-- persistence
INSERT INTO forecasts (organization_id, site_id, name, variable, issue_time_of_day,
lead_time_to_start, interval_label, interval_length, run_length,
interval_value_type, extra_parameters
) VALUES(
   @reforgid, @abqsite, 'Albuquerque NM Hour Ahead Persistence ac_power', 'ac_power', '00:00', 60, 'beginning', 60, 60, 'interval_mean' , CONCAT('{"is_reference_persistence_forecast": true, "index_persistence": true, "observation_id": "', BIN_TO_UUID(@abqobs, 1), '"}')
),(@reforgid, @nvsite, 'Henderson NV Hour Ahead Persistence ac_power', 'ac_power', '00:00', 60, 'beginning', 60, 60, 'interval_mean' , CONCAT('{"is_reference_persistence_forecast": true, "index_persistence": true, "observation_id": "', BIN_TO_UUID(@nvobs, 1), '"}')
),(@reforgid, @vtsite, 'Williston VT Hour Ahead Persistence ac_power', 'ac_power', '00:00', 60, 'beginning', 60, 60, 'interval_mean' , CONCAT('{"is_reference_persistence_forecast": true, "index_persistence": true, "observation_id": "', BIN_TO_UUID(@vtobs,1), '"}')
),(@reforgid, @flsite, 'Cocoa FL Hour Ahead Persistence ac_power', 'ac_power', '00:00', 60, 'beginning', 60, 60, 'interval_mean' , CONCAT('{"is_reference_persistence_forecast": true, "index_persistence": true, "observation_id": "', BIN_TO_UUID(@flobs, 1), '"}')
);


CREATE PROCEDURE doereport(IN name VARCHAR(64), IN siteid BINARY(16), IN reportid BINARY(16))
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE orgid BINARY(16);
    DECLARE baseparams JSON;
    DECLARE fxid CHAR(36);
    DECLARE obsid CHAR(36);
    DECLARE cur CURSOR FOR SELECT BIN_TO_UUID(id, 1) as id FROM forecasts WHERE site_id = siteid;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    SET baseparams = JSON_OBJECT('name', name, 'start', '2020-01-01T00:00Z', 'end', '2020-12-31T23:59Z', 'metrics', JSON_ARRAY('mae', 'rmse', 'mbe'), 'object_pairs', JSON_ARRAY());
    SET orgid = (SELECT organization_id FROM sites WHERE id = siteid);
    SET obsid = (SELECT BIN_TO_UUID(id, 1) FROM observations where site_id = siteid);

    OPEN cur;
    read_loop: LOOP
      FETCH cur INTO fxid;
      IF done THEN
        LEAVE read_loop;
      END IF;
      SET baseparams = JSON_ARRAY_APPEND(baseparams, '$.object_pairs', JSON_OBJECT('forecast', fxid, 'observation', obsid));
   END LOOP;
   CLOSE cur;
   INSERT INTO reports (id, organization_id, name, report_parameters) VALUES (reportid, orgid, name, baseparams);
END;


SET @abqrep = UUID_TO_BIN(UUID(), 1);
SET @nvrep = UUID_TO_BIN(UUID(), 1);
SET @vtrep = UUID_TO_BIN(UUID(), 1);
SET @flrep = UUID_TO_BIN(UUID(), 1);

CALL doereport('Albuquerque NM AC Power 2020 Report', @abqsite, @abqrep);
CALL doereport('Henderson NV AC Power 2020 Report', @nvsite, @nvrep);
CALL doereport('Williston VT AC Power 2020 Report', @vtsite, @vtrep);
CALL doereport('Cocoa FL AC Power 2020 Report', @flsite, @flrep);


DELETE FROM scheduled_jobs WHERE id = UUID_TO_BIN('907a9340-0b11-11ea-9e88-f4939feddd82', 1);
INSERT INTO scheduled_jobs (id, organization_id, user_id, name, job_type, parameters, schedule, version) VALUES (
    UUID_TO_BIN(UUID(), 1),
    @reforgid,
    @refid,
    'Reference data daily validation',
    'daily_observation_validation',
    JSON_OBJECT('start_td', '-28h', 'end_td', '0h', 'base_url', @baseurl),
    '{"type": "cron", "cron_string": "0 4 * * *"}',
    0
), (
    UUID_TO_BIN(UUID(), 1),
    @reforgid,
    @refid,
    'Reference NWP generation',
    'reference_nwp',
    JSON_OBJECT('issue_time_buffer', '10min', 'base_url', @baseurl),
    '{"type": "cron", "cron_string": "50 * * * *"}',
    0
), (
    UUID_TO_BIN(UUID(), 1),
    @reforgid,
    @refid,
    'Reference Persistence generation',
    'reference_persistence',
    JSON_OBJECT('base_url', @baseurl),
    '{"type": "cron", "cron_string": "*/30 * * * *"}',
    0
), (
    UUID_TO_BIN(UUID(), 1),
    @reforgid,
    @refid,
    'ABQ 2020 report',
    'periodic_report',
    JSON_OBJECT('report_id', BIN_TO_UUID(@abqrep, 1), 'base_url', @baseurl),
    '{"type": "cron", "cron_string": "0 7 * * *"}',
    0
), (
    UUID_TO_BIN(UUID(), 1),
    @reforgid,
    @refid,
    'Henderson 2020 report',
    'periodic_report',
    JSON_OBJECT('report_id', BIN_TO_UUID(@nvrep, 1), 'base_url', @baseurl),
    '{"type": "cron", "cron_string": "0 8 * * *"}',
    0
), (
    UUID_TO_BIN(UUID(), 1),
    @reforgid,
    @refid,
    'Williston 2020 report',
    'periodic_report',
    JSON_OBJECT('report_id', BIN_TO_UUID(@vtrep, 1), 'base_url', @baseurl),
    '{"type": "cron", "cron_string": "0 5 * * *"}',
    0
), (
    UUID_TO_BIN(UUID(), 1),
    @reforgid,
    @refid,
    'Cocoa 2020 report',
    'periodic_report',
    JSON_OBJECT('report_id', BIN_TO_UUID(@flrep, 1), 'base_url', @baseurl),
    '{"type": "cron", "cron_string": "0 5 * * *"}',
    0
);
