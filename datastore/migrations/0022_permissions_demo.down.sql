DELETE FROM arbiter_data.organizations WHERE name = 'Forecast Provider A';
DELETE FROM arbiter_data.organizations WHERE name = 'Forecast Provider B';
DELETE FROM arbiter_data.organizations WHERE name = 'Utility X';
DELETE FROM arbiter_data.roles WHERE name = 'Read Ashland Site';
DELETE FROM arbiter_data.permissions WHERE description = 'Read Ashland OR Site';
DELETE FROM arbiter_data.permissions WHERE description = 'Read Ashland OR Observations';
DELETE FROM arbiter_data.permissions WHERE description = 'Read Ashland OR Observation values';
