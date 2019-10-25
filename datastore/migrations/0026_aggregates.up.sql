ALTER TABLE arbiter_data.aggregates ADD COLUMN (
    description VARCHAR(255) NOT NULL,
    variable VARCHAR(32) NOT NULL,
    timezone VARCHAR(32) NOT NULL,
    interval_label ENUM('beginning', 'ending') NOT NULL,
    interval_length SMALLINT UNSIGNED NOT NULL,
    aggregate_type VARCHAR(32) NOT NULL,
    extra_parameters TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table to link aggregates and observations
CREATE TABLE arbiter_data.aggregate_observation_mapping(
    aggregate_id BINARY(16) NOT NULL,
    observation_id BINARY(16) NOT NULL,
    -- _incr allows observations to be removed and readded later
    _incr TINYINT UNSIGNED DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    /* add observation_deleted_at to track that an observation
       may not control. effective_until tracks when an
       observation is intentionally removed. The purpose of keeping
       both is that a user may be unaware that an observation is
       deleted, so the api can flag times after observation_deleted_at
       as invalid. The user can see this and update
       effective_until to ignore any data after this time
       without the flags.
       */
    effective_from TIMESTAMP,
    effective_until TIMESTAMP,
    observation_deleted_at TIMESTAMP,

    PRIMARY KEY (aggregate_id, observation_id, _incr),
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
    WHERE observation_id = OLD.id;
END;

GRANT SELECT(observation_id), UPDATE(observation_deleted_at) ON
   arbiter_data.aggregate_observation_mapping
   TO 'permission_trig'@'localhost';


CREATE DEFINER = 'select_objects'@'localhost' FUNCTION get_aggregate_observations (agg_id BINARY(16))
RETURNS JSON
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE jsonout JSON;
    SET jsonout = (
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'observation_id', BIN_TO_UUID(observation_id, 1),
            'created_at', created_at,
            'observation_deleted_at', observation_deleted_at,
            'effective_from', effective_from,
            'effective_until', effective_until))_
        FROM arbiter_data.aggregate_observation_mapping
        WHERE aggregate_id = agg_id GROUP BY aggregate_id
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
           name, description, variable,  timezone, interval_label,
           interval_length, 'interval_mean' as interval_value_type, aggregate_type,
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
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_aggregates (IN auth0id VARCHAR(32))
COMMENT 'List all aggregate metadata the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as aggregate_id,
    get_organization_name(organization_id) as provider,
    name, description, variable,  timezone, interval_label,
    interval_length, 'interval_mean' as interval_value_type, aggregate_type,
    extra_parameters, created_at, modified_at,
    get_aggregate_observations(id) as observations
    FROM arbiter_data.aggregates WHERE id IN (
        SELECT object_id from user_objects WHERE auth0_id = auth0id
        AND object_type = 'aggregates');

GRANT EXECUTE ON PROCEDURE arbiter_data.list_aggregates TO 'select_objects'@'localhost';

-- read aggregate values
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_aggregate_values (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN start TIMESTAMP, IN end TIMESTAMP)
COMMENT 'Read the observation values of the observations that make up the aggregate'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE maxend TIMESTAMP DEFAULT TIMESTAMP('2038-01-19 03:14:07');
    DECLARE minstart TIMESTAMP DEFAULT TIMESTAMP('1970-01-01 00:00:01');
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read_values'));
    IF allowed THEN
        -- In the future, this may be more complex, checking an aggregate_values table first
        -- before retrieving the individual observation objects
        WITH limits AS (
            SELECT observation_id, IFNULL(effective_from, minstart) as obs_start,
                LEAST(IFNULL(effective_until, maxend),
                      IFNULL(observation_deleted_at, maxend)) as obs_end
            FROM arbiter_data.aggregate_observation_mapping
            WHERE aggregate_id = binid AND can_user_perform_action(auth0id, observation_id, 'read_values')
        )
        SELECT BIN_TO_UUID(id, 1) as observation_id, timestamp, value, quality_flag
        FROM arbiter_data.observations_values JOIN limits
        WHERE id = limits.observation_id AND timestamp BETWEEN GREATEST(limits.obs_start, start) AND LEAST(limits.obs_end, end)
        GROUP BY id, timestamp ORDER BY id, timestamp;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read aggregate values"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE read_aggregate_values TO 'select_objects'@'localhost';

-- delete aggregate
CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_aggregate (
    IN auth0id VARCHAR(32), IN strid CHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'delete'));
    IF allowed THEN
        DELETE FROM arbiter_data.aggregates WHERE id = binid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "delete aggregate"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT SELECT(id), DELETE ON arbiter_data.aggregates TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE delete_aggregate TO 'delete_objects'@'localhost';


-- store aggregate
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_aggregate (
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN name VARCHAR(64),
    IN description VARCHAR(255), IN variable VARCHAR(32), IN timezone VARCHAR(32),
    IN interval_label VARCHAR(32), IN interval_length SMALLINT UNSIGNED,
    IN aggregate_type VARCHAR(32), IN extra_parameters TEXT)
COMMENT 'Create the aggregate object'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE orgid BINARY(16);
    DECLARE binid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SET allowed = (SELECT user_can_create(auth0id, 'aggregates'));
    IF allowed THEN
        SELECT get_user_organization(auth0id) INTO orgid;
        INSERT INTO arbiter_data.aggregates (
            id, organization_id, name, description, variable, timezone,
            interval_label, interval_length, aggregate_type, extra_parameters
        ) VALUES (
            binid, orgid, name, description, variable, timezone,
            interval_label, interval_length, aggregate_type, extra_parameters
        );
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "store aggregate"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT INSERT ON arbiter_data.aggregates TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE store_aggregate TO 'insert_objects'@'localhost';


-- add observation to aggregate
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE add_observation_to_aggregate (
    IN auth0id VARCHAR(32), IN agg_strid CHAR(36), IN obs_strid CHAR(36), IN effective_from TIMESTAMP)
COMMENT 'Adds an observation to an aggregate object. Must be able to read observation'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binaggid BINARY(16);
    DECLARE binobsid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE present BOOLEAN DEFAULT FALSE;
    DECLARE canreadobs BOOLEAN DEFAULT FALSE;
    DECLARE incr TINYINT DEFAULT 0;
    SET binaggid = UUID_TO_BIN(agg_strid, 1);
    SET binobsid = UUID_TO_BIN(obs_strid, 1);
    SET allowed = (SELECT can_user_perform_action(auth0id, binaggid, 'update'));
    IF allowed THEN
        SET present = (EXISTS(SELECT 1 FROM arbiter_data.aggregate_observation_mapping
            WHERE aggregate_id = binaggid AND observation_id = binobsid AND
            effective_until IS NULL));
        IF present THEN
            SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Adding observation to aggregate failed',
            MYSQL_ERRNO = 1142;
        ELSE
            SET canreadobs = (SELECT can_user_perform_action(auth0id, binobsid, 'read'));
            IF canreadobs THEN
                -- check if variables are the same
                SET incr = (SELECT IFNULL(MAX(_incr) + 1, 0) FROM arbiter_data.aggregate_observation_mapping
                            WHERE aggregate_id = binaggid AND observation_id = binobsid);
                INSERT INTO arbiter_data.aggregate_observation_mapping (aggregate_id, observation_id, _incr, effective_from)
                VALUES (binaggid, binobsid, incr, effective_from);
            ELSE
                SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not have permission to read observation',
                MYSQL_ERRNO = 1143;
            END IF;
        END IF;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "add observation to aggregate"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT INSERT, SELECT ON arbiter_data.aggregate_observation_mapping TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE add_observation_to_aggregate TO 'insert_objects'@'localhost';

-- remove observation from aggregate
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE remove_observation_from_aggregate(
    IN auth0id VARCHAR(32), IN agg_strid CHAR(36), IN obs_strid CHAR(36), IN until TIMESTAMP)
COMMENT 'Removes an observation to an aggregate object'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binaggid BINARY(16);
    DECLARE binobsid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    SET binaggid = UUID_TO_BIN(agg_strid, 1);
    SET binobsid = UUID_TO_BIN(obs_strid, 1);
    SET allowed = (SELECT can_user_perform_action(auth0id, binaggid, 'update'));
    IF allowed THEN
        UPDATE arbiter_data.aggregate_observation_mapping SET effective_until = until
        WHERE aggregate_id = binaggid AND observation_id = binobsid AND effective_until IS NULL;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "remove observation from aggregate"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT SELECT(aggregate_id, observation_id), UPDATE ON arbiter_data.aggregate_observation_mapping TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE remove_observation_from_aggregate TO 'insert_objects'@'localhost';


-- Redefine permissions functions to add aggregates

-- function to get organization of any non-rbac object
DROP FUNCTION IF EXISTS get_nonrbac_object_organization;
CREATE DEFINER = 'select_objects'@'localhost' FUNCTION get_nonrbac_object_organization (
    object_id BINARY(16), object_type VARCHAR(32))
RETURNS BINARY(16)
COMMENT 'Return the id of the organization for the object'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    IF object_type = 'sites' THEN
        RETURN (SELECT organization_id FROM arbiter_data.sites WHERE id = object_id);
    ELSEIF object_type = 'observations' THEN
        RETURN (SELECT organization_id FROM arbiter_data.observations WHERE id = object_id);
    ELSEIF object_type = 'forecasts' THEN
        RETURN (SELECT organization_id FROM arbiter_data.forecasts WHERE id = object_id);
    ELSEIF object_type = 'cdf_forecasts' THEN
        RETURN (SELECT organization_id FROM arbiter_data.cdf_forecasts_groups WHERE id = object_id);
    ELSEIF object_type = 'reports' THEN
        RETURN (SELECT organization_id FROM arbiter_data.reports WHERE id = object_id);
    ELSEIF object_type = 'aggregates' THEN
        RETURN (SELECT organization_id FROM arbiter_data.aggregates WHERE id = object_id);
    ELSE
        RETURN NULL;
    END IF;
END;
-- function to get organization of any object
DROP FUNCTION IF EXISTS get_object_organization;
CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_object_organization (
    object_id BINARY(16), object_type VARCHAR(32))
RETURNS BINARY(16)
COMMENT 'Return the id of the organization for the object'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    IF object_type in ('users', 'roles', 'permissions') THEN
        RETURN get_rbac_object_organization(object_id, object_type);
    ELSEIF object_type in ('sites', 'observations', 'forecasts', 'cdf_forecasts', 'reports', 'aggregates') THEN
        RETURN get_nonrbac_object_organization(object_id, object_type);
    ELSE
        RETURN NULL;
    END IF;
END;

GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'select_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'delete_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_object_organization TO 'update_rbac'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_nonrbac_object_organization TO 'select_objects'@'localhost';
GRANT EXECUTE ON FUNCTION arbiter_data.get_nonrbac_object_organization TO 'select_rbac'@'localhost';


-- test data
SET @aggid0 = UUID_TO_BIN('458ffc27-df0b-11e9-b622-62adb5fd6af0', 1);
SET @aggid1 = UUID_TO_BIN('d3d1e8e5-df1b-11e9-b622-62adb5fd6af0', 1);
SET @orgid = UUID_TO_BIN('b76ab62e-4fe1-11e9-9e44-64006a511e6f', 1);
SET @roleid = (SELECT id FROM arbiter_data.roles WHERE name = 'Test user role' and organization_id = @orgid);
INSERT INTO arbiter_data.aggregates (
    id, organization_id, name, variable, interval_label,
    interval_length, aggregate_type, extra_parameters, created_at, modified_at,
    description, timezone)
VALUES (
    @aggid0, @orgid,
    'Test Aggregate ghi', 'ghi', 'ending', 60, 'mean', 'extra',
    TIMESTAMP('2019-09-24 12:00'), TIMESTAMP('2019-09-24 12:00'),
    'ghi agg', 'America/Denver'
), (
    @aggid1, @orgid,
    'Test Aggregate dni', 'dni', 'ending', 60, 'mean', 'extra',
    TIMESTAMP('2019-09-24 12:00'), TIMESTAMP('2019-09-24 12:00'),
    'dni agg', 'America/Denver'
);

SET @created_at = TIMESTAMP('2019-09-25 00:00');
SET @effective_from = TIMESTAMP('2019-01-01 00:00');
INSERT INTO arbiter_data.aggregate_observation_mapping (
    aggregate_id, observation_id, created_at, effective_from) VALUES
    (@aggid0, UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440000', 1), @created_at, @effective_from),
    (@aggid0, UUID_TO_BIN('e0da0dea-9482-4073-84de-f1b12c304d23', 1), @created_at, @effective_from),
    (@aggid0, UUID_TO_BIN('b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2', 1), @created_at, @effective_from),
    (@aggid1, UUID_TO_BIN('9ce9715c-bd91-47b7-989f-50bb558f1eb9', 1), @created_at, @effective_from),
    (@aggid1, UUID_TO_BIN('95890740-824f-11e9-a81f-54bf64606445', 1), @created_at, @effective_from);

SET @pid0 = UUID_TO_BIN(UUID(), 1);
SET @pid1 = UUID_TO_BIN(UUID(), 1);
SET @pid2 = UUID_TO_BIN(UUID(), 1);
SET @pid3 = UUID_TO_BIN(UUID(), 1);
SET @pid4 = UUID_TO_BIN(UUID(), 1);

INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES
    (@pid0, 'Read Aggregates', @orgid, 'read', 'aggregates', TRUE),
    (@pid1, 'Read Aggregate Values', @orgid, 'read_values', 'aggregates', TRUE),
    (@pid2, 'Delete Aggregates', @orgid, 'delete', 'aggregates', TRUE),
    (@pid3, 'Update Aggregates', @orgid, 'update', 'aggregates', TRUE),
    (@pid4, 'Create aggregates', @orgid, 'create', 'aggregates', TRUE);

INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (@roleid, @pid0), (@roleid, @pid1), (@roleid, @pid2), (@roleid, @pid3), (@roleid, @pid4);

GRANT EXECUTE ON PROCEDURE arbiter_data.read_aggregate TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_aggregates TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_aggregate TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_aggregate TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_aggregate_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_observation_to_aggregate TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_observation_from_aggregate TO 'apiuser'@'%';
