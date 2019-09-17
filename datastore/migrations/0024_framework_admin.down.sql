DROP USER 'frameworkadmin'@'%';
DROP USER 'update_rbac'@'localhost';

DROP PROCEDURE IF EXISTS arbiter_data.create_organization;
DROP PROCEDURE IF EXISTS arbiter_data.create_default_read_role;
DROP PROCEDURE IF EXISTS arbiter_data.create_default_write_role;
DROP PROCEDURE IF EXISTS arbiter_data.create_default_create_role;
DROP PROCEDURE IF EXISTS arbiter_data.create_default_delete_role;
DROP PROCEDURE IF EXISTS arbiter_data.create_default_admin_role;
DROP PROCEDURE IF EXISTS arbiter_data.promote_user_to_org_admin;
DROP PROCEDURE IF EXISTS arbiter_data.add_user_to_org;
DROP PROCEDURE IF EXISTS arbiter_data.delete_user;
DROP PROCEDURE IF EXISTS arbiter_data.move_user_to_unaffiliated;
DROP PROCEDURE IF EXISTS arbiter_data.remove_org_roles_from_user;

DROP FUNCTION IF EXISTS arbiter_data.get_unaffiliated_orgid;
DROP FUNCTION IF EXISTS arbiter_data.get_org_role_by_name;
