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


CREATE DEFINER = 'select_objects'@'localhost' FUNCTION get_aggregate_observations (agg_id BINARY(16))
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
CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_aggregates (IN auth0id VARCHAR(32))
COMMENT 'List all aggregate metadata the user can read'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as aggregate_id,
    get_organization_name(organization_id) as provider,
    name, variable,  interval_label, interval_length,
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
    SET binid = UUID_TO_BIN(strid, 1);
    SET allowed = (SELECT can_user_perform_action(auth0id, binid, 'read_values'));
    IF allowed THEN
        -- In the future, this may be more complex, checking an aggregate_values table first
        -- before retrieving the individual observation objects
        SELECT BIN_TO_UUID(id, 1) as observation_id, timestamp, value, quality_flag FROM arbiter_data.observations_values
        WHERE id in (
            SELECT observation_id FROM arbiter_data.aggregate_observation_mapping
            WHERE aggregate_id = binid AND can_user_perform_action(auth0id, observation_id, 'read_values')) AND
        timestamp BETWEEN start AND end;
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
    IN auth0id VARCHAR(32), IN strid CHAR(36), IN name VARCHAR(64), IN variable VARCHAR(32),
    IN interval_label VARCHAR(32), IN interval_length SMALLINT UNSIGNED,
    IN extra_parameters TEXT)
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
            id, organization_id, name, variable, interval_label, interval_length, extra_parameters
        ) VALUES (
            binid, orgid, name, variable, interval_label, interval_length, extra_parameters
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
    IN auth0id VARCHAR(32), IN agg_strid CHAR(36), IN obs_strid CHAR(36))
COMMENT 'Adds an observation to an aggregate object. Must be able to read observation'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binaggid BINARY(16);
    DECLARE binobsid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;
    DECLARE canreadobs BOOLEAN DEFAULT FALSE;
    SET binaggid = UUID_TO_BIN(agg_strid, 1);
    SET binobsid = UUID_TO_BIN(obs_strid, 1);
    SET allowed = (SELECT can_user_perform_action(auth0id, binaggid, 'update'));
    IF allowed THEN
        SET canreadobs = (SELECT can_user_perform_action(auth0id, binobsid, 'read'));
        IF canreadobs THEN
            INSERT INTO arbiter_data.aggregate_observation_mapping (aggregate_id, observation_id)
            VALUES (binaggid, binobsid);
        ELSE
            SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'User does not have permission to read observation',
            MYSQL_ERRNO = 1143;
        END IF;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "add observation to aggregate"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT INSERT ON arbiter_data.aggregate_observation_mapping TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE add_observation_to_aggregate TO 'insert_objects'@'localhost';

-- remove observation from aggregate
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE remove_observation_from_aggregate(
    IN auth0id VARCHAR(32), IN agg_strid CHAR(36), IN obs_strid CHAR(36))
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
        UPDATE arbiter_data.aggregate_observation_mapping SET observation_removed_at = NOW()
        WHERE aggregate_id = binaggid AND observation_id = binobsid;
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
    interval_length, extra_parameters, created_at, modified_at)
VALUES (
    @aggid0, @orgid,
    'Test Aggregate ghi', 'ghi', 'ending', 60, 'extra',
    TIMESTAMP('2019-09-24 12:00'), TIMESTAMP('2019-09-24 12:00')
), (
    @aggid1, @orgid,
    'Test Aggregate dni', 'dni', 'ending', 60, 'extra',
    TIMESTAMP('2019-09-24 12:00'), TIMESTAMP('2019-09-24 12:00')
);

INSERT INTO arbiter_data.aggregate_observation_mapping (
    aggregate_id, observation_id) VALUES
    (@aggid0, UUID_TO_BIN('825fa193-824f-11e9-a81f-54bf64606445', 1)),
    (@aggid0, UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440000', 1)),
    (@aggid0, UUID_TO_BIN('e0da0dea-9482-4073-84de-f1b12c304d23', 1)),
    (@aggid0, UUID_TO_BIN('b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2', 1)),
    (@aggid1, UUID_TO_BIN('9ce9715c-bd91-47b7-989f-50bb558f1eb9', 1)),
    (@aggid1, UUID_TO_BIN('9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f', 1));

SET @pid0 = UUID_TO_BIN(UUID(), 1);
SET @pid1 = UUID_TO_BIN(UUID(), 1);
SET @pid2 = UUID_TO_BIN(UUID(), 1);
SET @pid3 = UUID_TO_BIN(UUID(), 1);

INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES
    (@pid0, 'Read Aggregates', @orgid, 'read', 'aggregates', TRUE),
    (@pid1, 'Read Aggregate Values', @orgid, 'read_values', 'aggregates', TRUE),
    (@pid2, 'Delete Aggregates', @orgid, 'delete', 'aggregates', TRUE),
    (@pid3, 'Update Aggregates', @orgid, 'update', 'aggregates', TRUE);

INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (@roleid, @pid0), (@roleid, @pid1), (@roleid, @pid2), (@roleid, @pid3);

GRANT EXECUTE ON PROCEDURE arbiter_data.read_aggregate TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_aggregates TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_aggregate TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_aggregate TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_aggregate_values TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.add_observation_to_aggregate TO 'apiuser'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.remove_observation_from_aggregate TO 'apiuser'@'%';
