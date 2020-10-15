SET @orgid = (SELECT id FROM organizations WHERE name = 'Organization 1');
SET @grant_permid = UUID_TO_BIN(UUID(), 1);
SET @revoke_permid = UUID_TO_BIN(UUID(), 1);
SET @read_permid = UUID_TO_BIN(UUID(), 1);

INSERT INTO arbiter_data.permissions(id, description, organization_id, action, object_type, applies_to_all) VALUES (
        @grant_permid, 'Role Granter', @orgid, 'grant', 'roles', TRUE), (
        @revoke_permid, 'Role Revoker', @orgid, 'revoke', 'roles', TRUE), (
        @read_permid, 'Read roles', @orgid, 'read', 'roles', TRUE);
        
SET @roleid = (SELECT id FROM roles WHERE name = 'Test user role');
INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (
    @roleid, @grant_permid),(
    @roleid, @revoke_permid),(
    @roleid, @read_permid);


SET @update_forecast = UUID_TO_BIN(UUID(), 1);
SET @update_observation = UUID_TO_BIN(UUID(), 1);
SET @update_site = UUID_TO_BIN(UUID(), 1);
SET @update_aggregate = UUID_TO_BIN(UUID(), 1);
SET @update_cdf = UUID_TO_BIN(UUID(), 1);

INSERT INTO arbiter_data.permissions(id, description, organization_id, action, object_type, applies_to_all) VALUES (
       @update_forecast, 'test user update forecast', @orgid, 'update', 'forecasts', FALSE),(
       @update_observation, 'test user update observation', @orgid, 'update', 'observations', FALSE),(
       @update_site, 'test user update site', @orgid, 'update', 'sites', FALSE),(
       @update_aggregate, 'test user update aggregate', @orgid, 'update', 'aggregates', FALSE),(
       @update_cdf, 'test user update cdf', @orgid, 'update', 'cdf_forecasts', FALSE);
       
INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)       VALUES (
    @update_forecast, UUID_TO_BIN('11c20780-76ae-4b11-bef1-7a75bdc784e3', 1)),(
    @update_observation, UUID_TO_BIN('123e4567-e89b-12d3-a456-426655440000', 1)),(
    @update_site, UUID_TO_BIN('d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a', 1)),(
    @update_aggregate, UUID_TO_BIN('458ffc27-df0b-11e9-b622-62adb5fd6af0', 1)),(
    @update_cdf, UUID_TO_BIN('ef51e87c-50b9-11e9-8647-d663bd873d93', 1));
        
INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (
    @roleid, @update_forecast),(
    @roleid, @update_observation),(
    @roleid, @update_site),(
    @roleid, @update_aggregate),(
    @roleid, @update_cdf);
