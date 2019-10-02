ALTER TABLE arbiter_data.aggregates DROP COLUMN variable,
DROP COLUMN interval_label, DROP COLUMN interval_length,
DROP COLUMN extra_parameters, DROP COLUMN created_at,
DROP COLUMN modified_at, DROP COLUMN aggregate_type,
DROP COLUMN description, DROP COLUMN timezone;
DELETE FROM arbiter_data.aggregates;

DROP TABLE arbiter_data.aggregate_observation_mapping;
DROP TRIGGER record_observation_deletion_in_aggregate_mapping;
DROP FUNCTION get_aggregate_observations;
DROP PROCEDURE read_aggregate;
REVOKE SELECT ON arbiter_data.aggregates FROM 'select_objects'@'localhost';
DROP PROCEDURE list_aggregates;
DROP PROCEDURE read_aggregate_values;
DROP PROCEDURE delete_aggregate;
DROP PROCEDURE store_aggregate;
DROP PROCEDURE add_observation_to_aggregate;
DROP PROCEDURE remove_observation_from_aggregate;
DROP FUNCTION get_nonrbac_object_organization;
DROP FUNCTION get_object_organization;


-- replace original rbac function definitions
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
    ELSE
        RETURN NULL;
    END IF;
END;

CREATE DEFINER = 'select_rbac'@'localhost' FUNCTION get_object_organization (
    object_id BINARY(16), object_type VARCHAR(32))
RETURNS BINARY(16)
COMMENT 'Return the id of the organization for the object'
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    IF object_type in ('users', 'roles', 'permissions') THEN
        RETURN get_rbac_object_organization(object_id, object_type);
    ELSEIF object_type in ('sites', 'observations', 'forecasts', 'cdf_forecasts', 'reports') THEN
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
