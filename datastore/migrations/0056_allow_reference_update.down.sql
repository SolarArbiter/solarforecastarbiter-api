-- Remove update permissions from reference user
SET @reforgid = get_organization_id('Reference');
SET @ref_update_role = (SELECT id FROM roles WHERE organization_id = @reforgid AND name = 'Update all');
SET @ref_user_id = (SELECT id FROM users WHERE auth0_id = 'auth0|5cc8aeff0ec8b510a4c7f2f1');

DELETE FROM arbiter_data.user_role_mapping WHERE user_id = @ref_user_id AND role_id = @ref_update_role;
