ALTER TABLE arbiter_data.forecasts CHANGE COLUMN interval_label interval_label ENUM('beginning', 'ending', 'instant', 'event') NOT NULL;
ALTER TABLE arbiter_data.observations CHANGE COLUMN interval_label interval_label ENUM('beginning', 'ending', 'instant', 'event') NOT NULL;
ALTER TABLE arbiter_data.cdf_forecasts_groups CHANGE COLUMN interval_label interval_label ENUM('beginning', 'ending', 'instant', 'event') NOT NULL;
ALTER TABLE arbiter_data.aggregates CHANGE COLUMN interval_label interval_label ENUM('beginning', 'ending', 'instant', 'event') NOT NULL;


SET @orgid = (SELECT id FROM organizations WHERE name = 'Organization 1');
SET @event_fx_id = UUID_TO_BIN('24cbae4e-7ea6-11ea-86b1-0242ac150002', 1);
SET @site_id = UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440001', 1);

INSERT INTO arbiter_data.forecasts (
    id, organization_id, site_id, name, variable, issue_time_of_day,
    lead_time_to_start, interval_label, interval_length, run_length,
    interval_value_type, extra_parameters
) VALUES (
    @event_fx_id, @orgid, @site_id, "Weather Station Event Forecast", "event",
    "05:00", 60.0, "event", 5, 60.0, "instantaneous", ""
);
