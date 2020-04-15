-- Remove any event values
DELETE FROM arbiter_data.forecasts_values WHERE id IN (SELECT id from arbiter_data.forecasts WHERE interval_label = 'event');
DELETE FROM arbiter_data.observations_values WHERE id IN (SELECT id from arbiter_data.observations WHERE interval_label = 'event');
DELETE FROM arbiter_data.cdf_forecasts_values WHERE id IN (
    SELECT id from arbiter_data.cdf_forecasts_singles WHERE cdf_forecast_group_id IN (
        SELECT id from arbiter_data.cdf_forecasts_groups WHERE interval_label = 'event')
);

-- Remove any event metadata
DELETE FROM arbiter_data.forecasts WHERE interval_label = 'event';
DELETE FROM arbiter_data.cdf_forecasts_groups WHERE interval_label = 'event';
DELETE FROM arbiter_data.observations WHERE interval_label = 'event';
DELETE FROM arbiter_data.aggregates WHERE interval_label = 'event';

ALTER TABLE arbiter_data.forecasts CHANGE COLUMN interval_label interval_label ENUM('beginning', 'ending', 'instant', 'event') NOT NULL;
ALTER TABLE arbiter_data.observations CHANGE COLUMN interval_label interval_label ENUM('beginning', 'ending', 'instant', 'event') NOT NULL;
ALTER TABLE arbiter_data.cdf_forecasts_groups CHANGE COLUMN interval_label interval_label ENUM('beginning', 'ending', 'instant', 'event') NOT NULL;
ALTER TABLE arbiter_data.aggregates CHANGE COLUMN interval_label interval_label ENUM('beginning', 'ending', 'instant', 'event') NOT NULL;
