-- Create the organizations table
CREATE TABLE arbiter_data.organizations (
  name VARCHAR(32) NOT NULL UNIQUE,
  id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
  accepted_tou BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED
;
-- Create the users table
CREATE TABLE arbiter_data.users (
  id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
  auth0_id VARCHAR(32) NOT NULL UNIQUE, -- will auth0 tokens always be 24 characters after auth0|?
  organization_id BINARY(16) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY (organization_id),
  /* define organization_id as a foreign key so that the user is deleted when the
     organization is deleted */
  FOREIGN KEY (organization_id)
    REFERENCES organizations(id)
    ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

-- Create the roles table
CREATE TABLE arbiter_data.roles (
  name VARCHAR(64) NOT NULL UNIQUE,
  description VARCHAR(255) NOT NULL,
  id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
  organization_id BINARY(16) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY (organization_id),
  FOREIGN KEY (organization_id)
    REFERENCES organizations(id)
    ON DELETE CASCADE ON UPDATE RESTRICT

) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

-- Create the mapping between users and roles
CREATE TABLE arbiter_data.user_role_mapping (
  user_id BINARY(16) NOT NULL,
  role_id BINARY(16) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (user_id, role_id),
  FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE RESTRICT,
  FOREIGN KEY (role_id)
    REFERENCES roles(id)
    ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

-- Create the permissions table. Permissions can be set on specific objects or all objects of a type
CREATE TABLE arbiter_data.permissions (
  id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
  description VARCHAR(64) NOT NULL,
  organization_id BINARY(16) NOT NULL,
  action ENUM('create', 'read', 'update',  'delete') NOT NULL,
  object_type ENUM('sites', 'aggregates', 'forecasts', 'observations', 'users', 'roles', 'permissions') NOT NULL,
  applies_to_all BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY (action, object_type),
  KEY (organization_id),
  FOREIGN KEY (organization_id)
    REFERENCES organizations(id)
    ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

-- Create the mapping between roles and permissions
CREATE TABLE arbiter_data.role_permission_mapping (
  role_id BINARY(16) NOT NULL,
  permission_id BINARY(16) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (role_id, permission_id),
  FOREIGN KEY (role_id)
    REFERENCES roles(id)
    ON DELETE CASCADE ON UPDATE RESTRICT,
  FOREIGN KEY (permission_id)
    REFERENCES permissions(id)
    ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;



-- Create the mapping between permissions and objects
CREATE TABLE arbiter_data.permission_object_mapping (
  permission_id BINARY(16) NOT NULL,
  object_id BINARY(16) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (permission_id, object_id),
  KEY (object_id),
  -- cannot set foreign key on object_id since it could be from any table
  FOREIGN KEY (permission_id)
    REFERENCES permissions(id)
    ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;
