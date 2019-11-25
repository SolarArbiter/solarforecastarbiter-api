SET @reforgid = (SELECT id FROM organizations WHERE name = 'Reference');

-- allow everyone to read reference reports
SET @readrep = UUID_TO_BIN(UUID(), 1);
SET @readrepval = UUID_TO_BIN(UUID(), 1);
SET @readrole = (SELECT id from roles WHERE name = 'Read Reference Data' and organization_id = @reforgid);

INSERT INTO permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
  @readrep, 'Read all reports', @reforgid, 'read', 'reports', TRUE), (
  @readrepval, 'Read all report values', @reforgid, 'read_values', 'reports', TRUE);

INSERT INTO role_permission_mapping (role_id, permission_id) VALUES (@readrole, @readrep), (@readrole, @readrepval);

-- allow reference to create/update reports
SET @createrep = UUID_TO_BIN(UUID(), 1);
SET @updaterep = UUID_TO_BIN(UUID(), 1);
SET @writerep = UUID_TO_BIN(UUID(), 1);
SET @refrole = (SELECT id from roles WHERE name = 'Reference user role' and organization_id = @reforgid);

INSERT INTO permissions (id, description, organization_id, action, object_type, applies_to_all) VALUES (
  @createrep, 'Create all reports', @reforgid, 'create', 'reports', TRUE),(
  @updaterep, 'Update all reports', @reforgid, 'update', 'reports', TRUE),(
  @writerep, 'Create all report values', @reforgid, 'write_values', 'reports', TRUE);

INSERT INTO role_permission_mapping (role_id, permission_id) VALUES (@refrole, @createrep), (@refrole, @updaterep), (@refrole, @writerep), (@refrole, @readrep), (@refrole, @readrepval);
