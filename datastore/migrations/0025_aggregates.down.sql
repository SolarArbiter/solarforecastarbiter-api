ALTER TABLE arbiter_data.aggregates DROP COLUMN variable,
DROP COLUMN interval_label, DROP COLUMN interval_length,
DROP COLUMN extra_parameters, DROP COLUMN created_at,
DROP COLUMN modified_at;
DELETE FROM arbiter_data.aggregates;

DROP TABLE arbiter_data.aggregate_observation_mapping;
DROP TRIGGER record_observation_deletion_in_aggregate_mapping;
DROP FUNCTION get_aggregate_observations;
DROP PROCEDURE read_aggregate;
REVOKE SELECT ON arbiter_data.aggregates FROM 'select_objects'@'localhost';
