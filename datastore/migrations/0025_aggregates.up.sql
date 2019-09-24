ALTER TABLE arbiter_data.aggregates ADD COLUMN (
    variable VARCHAR(32) NOT NULL,
    -- aggregates shouldn't be instant, hard to align
    -- observations
    interval_label ENUM('beginning', 'ending') NOT NULL,
    interval_length SMALLINT UNSIGNED NOT NULL,
    -- do we want to support more than sum?
    -- interval_value_type VARCHAR(32) NOT NULL,
    extra_parameters TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
);

-- Table to link aggregates and observations
CREATE TABLE arbiter_data.aggregate_observation_mapping(
    aggregate_id BINARY(16) NOT NULL,
    observation_id BINARY(16) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    /* add observation_deleted_at to track that an observation
       can be removed but the aggregate object may still exist
       enables support of aggregates of objects that a user
       may not control */
    observation_deleted_at TIMESTAMP,

    PRIMARY KEY (aggregate_id, observation_id),
    KEY (observation_id),
    FOREIGN KEY (aggregate_id)
        REFERENCES aggregates(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

-- how will aggregates work with forecasts?
-- see also fail_on_aggregate_delete_if_forecast in 0005

CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER
    record_observation_deletion_in_aggregate_mapping
BEFORE DELETE ON arbiter_data.observations
FOR EACH ROW
BEGIN
    UPDATE arbiter_data.aggregate_observation_mapping
    SET observation_deleted_at = CURRENT_TIMESTAMP()
    WHERE observation_id = OLD.id
END;

GRANT SELECT(observation_id), UPDATE(observation_deleted_at) ON
    arbiter_data.aggregate_observation_mapping
   TO 'permission_trig'@'localhost';


-- read aggregates
-- list aggregates
-- read aggregate values
-- delete aggregate
-- add observation to aggregate
