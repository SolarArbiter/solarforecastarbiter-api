-- Add update permissions to reference user to allow turning on/off reference data
SET @reforgid = get_organization_id('Reference');
SET @ref_update_role = (SELECT id FROM roles WHERE organization_id = @reforgid AND name = 'Update all');
SET @ref_user_id = (SELECT id FROM users WHERE auth0_id = 'auth0|5cc8aeff0ec8b510a4c7f2f1');

INSERT INTO arbiter_data.user_role_mapping (user_id, role_id) VALUES (@ref_user_id, @ref_update_role);
