-- create user for triggers and don't allow this user to log in to the server
CREATE USER 'permission_trig'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;
GRANT SELECT, TRIGGER ON arbiter_data.sites TO 'permission_trig'@'localhost';
GRANT SELECT, TRIGGER ON arbiter_data.aggregates TO 'permission_trig'@'localhost';
GRANT SELECT, TRIGGER ON arbiter_data.forecasts TO 'permission_trig'@'localhost';
GRANT SELECT, TRIGGER ON arbiter_data.observations TO 'permission_trig'@'localhost';
GRANT SELECT, TRIGGER ON arbiter_data.users TO 'permission_trig'@'localhost';
GRANT SELECT, TRIGGER ON arbiter_data.roles TO 'permission_trig'@'localhost';
GRANT SELECT, TRIGGER ON arbiter_data.permissions TO 'permission_trig'@'localhost';
GRANT INSERT, SELECT, DELETE ON arbiter_data.permission_object_mapping TO 'permission_trig'@'localhost';

-- Insert all current objects of a type when applies_to_all is True into permission_object_table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER add_object_perm_on_permissions_insert AFTER INSERT ON arbiter_data.permissions
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
    -- make sure any new permission gets added to an existing applies_to_all which references permissions
    INSERT IGNORE INTO arbiter_data.permission_object_mapping (permission_id, object_id)
        SELECT id, NEW.id from arbiter_data.permissions WHERE action !='create'
            AND applies_to_all AND organization_id = NEW.organization_id and object_type = 'permissions';
END;


-- make the permissions table un-updatable to permission_object_mapping issues
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER no_permissions_update BEFORE UPDATE ON arbiter_data.permissions
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'The permissions table can not be updated', MYSQL_ERRNO = 1216;
END;

-- permission delete handled by foreign key constraint

-- add trigger for inserts to sites table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER add_object_perm_on_sites_insert AFTER INSERT ON arbiter_data.sites
FOR EACH ROW INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
    SELECT id, NEW.id FROM arbiter_data.permissions WHERE action != 'create' AND applies_to_all AND organization_id = NEW.organization_id AND object_type = 'sites';


-- add trigger for inserts to aggregates table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER add_object_perm_on_aggregates_insert AFTER INSERT ON arbiter_data.aggregates
FOR EACH ROW INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
    SELECT id, NEW.id FROM arbiter_data.permissions WHERE action != 'create' AND applies_to_all AND organization_id = NEW.organization_id AND object_type = 'aggregates';


-- add trigger for inserts to forecasts table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER add_object_perm_on_forecasts_insert AFTER INSERT ON arbiter_data.forecasts
FOR EACH ROW INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
    SELECT id, NEW.id FROM arbiter_data.permissions WHERE action != 'create' AND applies_to_all AND organization_id = NEW.organization_id AND object_type = 'forecasts';


-- add trigger for inserts to observations table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER add_object_perm_on_observations_insert AFTER INSERT ON arbiter_data.observations
FOR EACH ROW INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
    SELECT id, NEW.id FROM arbiter_data.permissions WHERE action != 'create' AND applies_to_all AND organization_id = NEW.organization_id AND object_type = 'observations';


-- add trigger for inserts to users table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER add_object_perm_on_users_insert AFTER INSERT ON arbiter_data.users
FOR EACH ROW INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
    SELECT id, NEW.id FROM arbiter_data.permissions WHERE action != 'create' AND applies_to_all AND organization_id = NEW.organization_id AND object_type = 'users';


-- add trigger for inserts to roles table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER add_object_perm_on_roles_insert AFTER INSERT ON arbiter_data.roles
FOR EACH ROW INSERT INTO arbiter_data.permission_object_mapping (permission_id, object_id)
    SELECT id, NEW.id FROM arbiter_data.permissions WHERE action != 'create' AND applies_to_all AND organization_id = NEW.organization_id AND object_type = 'roles';


-- add trigger for deletion from observations table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_object_perm_on_observations_delete AFTER DELETE ON arbiter_data.observations
FOR EACH ROW DELETE FROM arbiter_data.permission_object_mapping WHERE object_id = OLD.id;


-- add trigger for deletion from forecasts table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_object_perm_on_forecasts_delete AFTER DELETE ON arbiter_data.forecasts
FOR EACH ROW DELETE FROM arbiter_data.permission_object_mapping WHERE object_id = OLD.id;


-- add trigger for deletion from aggregates table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_object_perm_on_aggregates_delete AFTER DELETE ON arbiter_data.aggregates
FOR EACH ROW DELETE FROM arbiter_data.permission_object_mapping WHERE object_id = OLD.id;


-- add trigger for deletion from users table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_object_perm_on_users_delete AFTER DELETE ON arbiter_data.users
FOR EACH ROW DELETE FROM arbiter_data.permission_object_mapping WHERE object_id = OLD.id;


-- add trigger for deletion from roles table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_object_perm_on_roles_delete AFTER DELETE ON arbiter_data.roles
FOR EACH ROW DELETE FROM arbiter_data.permission_object_mapping WHERE object_id = OLD.id;


-- add trigger for deletion from sites table
CREATE DEFINER = 'permission_trig'@'localhost' TRIGGER remove_object_perm_on_sites_delete AFTER DELETE ON arbiter_data.sites
FOR EACH ROW DELETE FROM arbiter_data.permission_object_mapping WHERE object_id = OLD.id;
