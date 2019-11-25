SET @reforgid = (SELECT id FROM organizations WHERE name = 'Reference');
DROP PROCEDURE doereport;
DROP PROCEDURE makecvs;

DELETE FROM reports WHERE organization_id = @reforgid;
DELETE FROM observations WHERE organization_id = @reforgid AND name in (
  'Albuquerque NM ac_power', 'Henderson NV ac_power', 'Williston VT ac_power', 'Cocoa FL ac_power');
DELETE FROM cdf_forecasts_groups WHERE organization_id = @reforgid AND (
  name like 'Albuquerque NM%ac_power'
  OR name like 'Henderson NV%ac_power'
  OR name like 'Williston VT%ac_power'
  OR name like 'Cocoa FL%ac_power');
DELETE FROM forecasts WHERE organization_id = @reforgid AND (
  name like 'Albuquerque NM%ac_power'
  OR name like 'Henderson NV%ac_power'
  OR name like 'Williston VT%ac_power'
  OR name like 'Cocoa FL%ac_power');
DELETE FROM sites WHERE organization_id = @reforgid AND name in (
  'DOE RTC Albuquerque NM', 'DOE RTC Henderson NV', 'DOE RTC Williston VT', 'DOE RTC Cocoa FL');
DELETE FROM scheduled_jobs WHERE organization_id = @reforgid;
INSERT INTO scheduled_jobs (id, organization_id, user_id, name, job_type, parameters, schedule, version) VALUES (
    UUID_TO_BIN('907a9340-0b11-11ea-9e88-f4939feddd82', 1),
    UUID_TO_BIN('b76ab62e-4fe1-11e9-9e44-64006a511e6f', 1),
    UUID_TO_BIN('0c90950a-7cca-11e9-a81f-54bf64606445', 1),
    'Test Job',
    'daily_observation_validation', '{"start_td": "-1d", "end_td": "0h", "base_url": "http://localhost:5000"}',
    '{"type": "cron", "cron_string": "0 0 * * *"}',
    0);
