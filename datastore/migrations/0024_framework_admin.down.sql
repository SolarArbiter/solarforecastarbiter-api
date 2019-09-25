DROP USER 'frameworkadmin'@'%';
DROP USER 'update_rbac'@'localhost';

ALTER TABLE arbiter_data.roles DROP INDEX organization_role;
ALTER TABLE arbiter_data.roles ADD UNIQUE name (name);

DROP PROCEDURE arbiter_data.create_organization;
DROP PROCEDURE arbiter_data.create_default_read_role;
DROP PROCEDURE arbiter_data.create_default_write_role;
DROP PROCEDURE arbiter_data.create_default_create_role;
DROP PROCEDURE arbiter_data.create_default_delete_role;
DROP PROCEDURE arbiter_data.create_default_admin_role;
DROP PROCEDURE arbiter_data.promote_user_to_org_admin;
DROP PROCEDURE arbiter_data.add_user_to_org;
DROP PROCEDURE arbiter_data.delete_user;
DROP PROCEDURE arbiter_data.move_user_to_unaffiliated;
DROP PROCEDURE arbiter_data.remove_org_roles_from_user;
DROP PROCEDURE arbiter_data.list_all_users;
DROP PROCEDURE arbiter_data.list_all_organizations;
DROP PROCEDURE arbiter_data.set_org_accepted_tou;

DROP FUNCTION arbiter_data.get_org_role_by_name;
