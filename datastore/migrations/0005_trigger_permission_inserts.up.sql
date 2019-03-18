-- create user for triggers and don't allow this user to log in to the server
CREATE USER 'permission_trigger'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;
GRANT SELECT ON arbiter_data.sites TO 'permission_trigger'@'localhost';
GRANT SELECT ON arbiter_data.aggregates TO 'permission_trigger'@'localhost';
GRANT SELECT ON arbiter_data.forecasts TO 'permission_trigger'@'localhost';
GRANT SELECT ON arbiter_data.observations TO 'permission_trigger'@'localhost';
GRANT SELECT ON arbiter_data.users TO 'permission_trigger'@'localhost';
GRANT SELECT ON arbiter_data.roles TO 'permission_trigger'@'localhost';
GRANT SELECT ON arbiter_data.permissions TO 'permission_trigger'@'localhost';
GRANT INSERT, SELECT, DELETE ON arbiter_data.permission_object_mapping TO 'permssion_trigger'@'localhost';


-- Insert all current objects of a type when applies_to_all is True into permission_object_table
CREATE DEFINER = 'permission_trigger'@'localhost' TRIGGER add_object_perm_on_permissions_insert AFTER INSERT ON arbiter_data.permissions
FOR EACH ROW
BEGIN
    IF NEW.applies_to_all AND NEW.action != 'create' THEN
        IF NEW.object_type = 'sites' THEN
            INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
                SELECT NEW.id, id FROM arbiter_data.sites WHERE organization_id = NEW.organization_id;
        ELSEIF NEW.object_type = 'aggregates' THEN
            INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
                SELECT NEW.id, id FROM arbiter_data.aggregates WHERE organization_id = NEW.organization_id;
        ELSEIF NEW.object_type = 'forecasts' THEN
            INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
                SELECT NEW.id, id FROM arbiter_data.forecasts WHERE organization_id = NEW.organization_id;
        ELSEIF NEW.object_type = 'observations' THEN
            INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
                SELECT NEW.id, id FROM arbiter_data.observations WHERE organization_id = NEW.organization_id;
        ELSEIF NEW.object_type = 'users' THEN
            INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
                SELECT NEW.id, id FROM arbiter_data.users WHERE organization_id = NEW.organization_id;
        ELSEIF NEW.object_type = 'roles' THEN
            INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
                SELECT NEW.id, id FROM arbiter_data.roles WHERE organization_id = NEW.organization_id;
        ELSEIF NEW.object_type = 'permissions' THEN
            INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
                SELECT NEW.id, id FROM arbiter_data.permissions WHERE organization_id = NEW.organization_id;
        END IF;
    END IF;
END;


-- make the permissions table un-updatable to permission_object_mapping issues
CREATE DEFINER = 'permission_trigger'@'localhost' TRIGGER no_permssions_update BEFORE UPDATE ON arbiter_data.permissions
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'The permissions table can not be updated', MYSQL_ERRNO = 1216;
END;

-- permission delete handled by foreign key constraint
