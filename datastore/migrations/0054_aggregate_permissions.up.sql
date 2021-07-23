SET @orgid = get_organization_id('Reference');
SET @refrole = get_reference_role_id();
SET @refuser_role = (SELECT id FROM arbiter_data.roles WHERE name = 'Reference user role' AND organization_id = @orgid);

SET @agg_read = UUID_TO_BIN(UUID(), 1);
SET @agg_read_vals = UUID_TO_BIN(UUID(), 1);
SET @agg_create = UUID_TO_BIN(UUID(), 1);
SET @agg_update = UUID_TO_BIN(UUID(), 1);

INSERT INTO arbiter_data.permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
    @agg_read, 'Read aggregates', @orgid, 'read', 'aggregates', TRUE), (
    @agg_read_vals, 'Read aggregate values', @orgid, 'read_values', 'aggregates', TRUE), (
    @agg_create, 'Create aggregates', @orgid, 'create', 'aggregates', TRUE), (
    @agg_update, 'Update aggregates', @orgid, 'update', 'aggregates', TRUE);

INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (
    @refrole, @agg_read), (
    @refrole, @agg_read_vals), (
    @refuser_role, @agg_read), (
    @refuser_role, @agg_read_vals), (
    @refuser_role, @agg_create), (
    @refuser_role, @agg_update);
