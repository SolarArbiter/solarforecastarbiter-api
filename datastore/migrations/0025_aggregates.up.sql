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
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table to link aggregates and observations
CREATE TABLE arbiter_data.aggregate_observation_mapping(
    aggregate_id BINARY(16) NOT NULL,
    observation_id BINARY(16) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    /* add observation_removed_at to track that an observation
       can be removed but the aggregate object may still exist
       enables support of aggregates of objects that a user
       may not control */
    observation_removed_at TIMESTAMP,

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
    SET observation_removed_at = CURRENT_TIMESTAMP()
    WHERE observation_id = OLD.id;
END;

GRANT SELECT(observation_id), UPDATE(observation_removed_at) ON
   arbiter_data.aggregate_observation_mapping
   TO 'permission_trig'@'localhost';


CREATE DEFINER = 'select_objects'@'localhost' FUNCTION get_aggregate_observations (aggregate_id BINARY(16))
RETURNS JSON
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE jsonout JSON;
    SET jsonout = (
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'observation_id', BIN_TO_UUID(observation_id, 1),
            'created_at', created_at,
            'observation_removed_at', observation_removed_at))_
        FROM arbiter_data.aggregate_observation_mapping
        WHERE aggregate_id = aggregate_id GROUP BY aggregate_id
    );
    IF jsonout is NOT NULL THEN
        RETURN jsonout;
    ELSE
        RETURN JSON_ARRAY();
    END IF;
END;

GRANT SELECT ON arbiter_data.aggregate_observation_mapping TO 'select_objects'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_aggregate_observations TO 'select_objects'@'localhost';

-- read aggregates
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_aggregate (
   IN auth0id VARCHAR(32), IN strid CHAR(36))
COMMENT 'Read aggregate metadata'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read'));
    IF allowed THEN
       SELECT BIN_TO_UUID(id, 1) as aggregate_id,
           get_organization_name(organization_id) as provider,
           name, variable,  interval_label, interval_length,
           extra_parameters, created_at, modified_at,
           get_aggregate_observations(id) as observations
       FROM arbiter_data.aggregates WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read aggregate"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT SELECT on arbiter_data.aggregates to 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_aggregate TO 'select_objects'@'localhost';

-- list aggregates
-- read aggregate values
-- delete aggregate
-- add observation to aggregate

SET @aggid = UUID_TO_BIN('458ffc27-df0b-11e9-b622-62adb5fd6af0', 1);
SET @orgid = UUID_TO_BIN('b76ab62e-4fe1-11e9-9e44-64006a511e6f', 1);
SET @roleid = (SELECT id FROM arbiter_data.roles WHERE name = 'Test user role' and organization_id = @orgid);
INSERT INTO arbiter_data.aggregates (
    id, organization_id, name, variable, interval_label,
    interval_length, extra_parameters, created_at, modified_at)
VALUES (
    @aggid, @orgid,
    'Test Aggregate', 'ghi', 'ending', 60, 'extra',
    TIMESTAMP('2019-09-24 12:00'), TIMESTAMP('2019-09-24 12:00')
);

INSERT INTO arbiter_data.aggregate_observation_mapping (
    aggregate_id, observation_id) VALUES
    (@aggid, UUID_TO_BIN('825fa193-824f-11e9-a81f-54bf64606445', 1)),
    (@aggid, UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440000', 1)),
    (@aggid, UUID_TO_BIN('e0da0dea-9482-4073-84de-f1b12c304d23', 1)),
    (@aggid, UUID_TO_BIN('b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2', 1));

SET @pid0 = UUID_TO_BIN(UUID(), 1);

INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
    @pid0, 'Read Aggregates', @orgid, 'read', 'aggregates', TRUE);

INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (@roleid, @pid0);

GRANT EXECUTE ON PROCEDURE arbiter_data.read_aggregate TO 'apiuser'@'%';
