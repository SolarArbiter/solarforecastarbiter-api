DELETE FROM arbiter_data.organizations WHERE name = 'Forecast Provider A';
DELETE FROM arbiter_data.organizations WHERE name = 'Forecast Provider B';
DELETE FROM arbiter_data.organizations WHERE name = 'Utility X';
DELETE FROM arbiter_data.roles WHERE name = 'Read Weather Station Site';
DELETE FROM arbiter_data.permissions WHERE description = 'Read Weather Station Site';
DELETE FROM arbiter_data.permissions WHERE description = 'Read Weather Station Observations';
DELETE FROM arbiter_data.permissions WHERE description = 'Read Weather Station Observation values';
