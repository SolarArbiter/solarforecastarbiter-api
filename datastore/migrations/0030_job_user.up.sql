CREATE TABLE arbiter_data.job_tokens(
  id BINARY(16) NOT NULL,
  token VARCHAR(256) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  FOREIGN KEY (id)
    REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


CREATE USER 'token_user'@'localhost' IDENTIFIED WITH caching_sha2_password as '$A$005$THISISACOMBINATIONOFINVALIDSALTANDPASSWORDTHATMUSTNEVERBRBEUSED' ACCOUNT LOCK;


CREATE DEFINER = 'token_user'@'localhost' PROCEDURE store_token (IN auth0id VARCHAR(32), IN token VARCHAR(256))
COMMENT 'Store the encrypted token in the table'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE user_id BINARY(16);
    SET user_id = (SELECT id FROM arbiter_data.users WHERE auth0_id = auth0id);
    INSERT INTO arbiter_data.job_tokens (id, token) VALUES (user_id, token)
      ON DUPLICATE KEY UPDATE token = VALUES(token);
END;

GRANT SELECT(id, auth0_id) ON arbiter_data.users TO 'token_user'@'localhost';
GRANT SELECT, INSERT, UPDATE(token) ON arbiter_data.job_tokens TO 'token_user'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_token TO 'token_user'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_token TO 'frameworkadmin'@'%';


CREATE DEFINER = 'insert_rbac'@'localhost' PROCEDURE create_job_user(IN auth0id VARCHAR(32), IN orgid CHAR(36))
COMMENT 'Inserts a new job user into the organization and add permission to read reference data only, returning new user id'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE userid BINARY(16);
    DECLARE binorgid BINARY(16);
    SET userid = UUID_TO_BIN(UUID(), 1);
    SET binorgid = UUID_TO_BIN(orgid, 1);
    INSERT INTO arbiter_data.users (id, auth0_id, organization_id) VALUES (
        userid, auth0id, binorgid);
    CALL arbiter_data.add_reference_role_to_user(userid);
    CALL arbiter_data.create_default_user_role(userid, binorgid);
    SELECT BIN_TO_UUID(userid, 1);
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.create_job_user TO 'insert_rbac'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.create_job_user TO 'frameworkadmin'@'%';
