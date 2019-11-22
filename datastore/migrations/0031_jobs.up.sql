CREATE TABLE arbiter_data.scheduled_jobs (
    id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
    organization_id BINARY(16) NOT NULL,
    user_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,
    job_type VARCHAR(64) NOT NULL,
    parameters JSON NOT NULL,
    schedule JSON NOT NULL,
    version TINYINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY primary_id (id),
    UNIQUE name_org_unq (organization_id, name),
    FOREIGN KEY job_user_fk (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    FOREIGN KEY job_org_fk (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


CREATE USER 'job_executor'@'%' IDENTIFIED BY 'thisisaterribleandpublicpassword';


CREATE DEFINER = 'token_user'@'localhost' PROCEDURE fetch_token (IN user_id CHAR(36))
COMMENT 'Fetch the refresh token for the user'
READS SQL DATA SQL SECURITY DEFINER
SELECT token FROM arbiter_data.job_tokens WHERE id = UUID_TO_BIN(user_id, 1);

GRANT EXECUTE ON PROCEDURE arbiter_data.fetch_token TO 'token_user'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.fetch_token TO 'job_executor'@'%';


CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_job (
    IN strid CHAR(36), IN userstrid CHAR(36), IN name VARCHAR(64), IN job_type VARCHAR(64),
    IN parameters JSON, IN schedule JSON, IN version TINYINT)
COMMENT 'Create a scheduled job object'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    DECLARE userid BINARY(16);
    DECLARE orgid BINARY(16);
    SET binid = UUID_TO_BIN(strid, 1);
    SET userid = UUID_TO_BIN(userstrid, 1);
    SET orgid = get_object_organization(userid, 'users');

    INSERT INTO arbiter_data.scheduled_jobs (id, organization_id, user_id, name, job_type,
        parameters, schedule, version) VALUES (binid, orgid, userid, name, job_type, parameters,
        schedule, version);
END;

GRANT INSERT ON arbiter_data.scheduled_jobs TO 'insert_objects'@'localhost';
GRANT EXECUTE ON FUNCTION get_object_organization TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_job TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_job TO 'frameworkadmin'@'%';


CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_jobs ()
COMMENT 'List the jobs of an organization'
READS SQL DATA SQL SECURITY DEFINER
SELECT BIN_TO_UUID(id, 1) as id, get_organization_name(organization_id) as organization_name,
    BIN_TO_UUID(organization_id, 1) as organization_id,
    BIN_TO_UUID(user_id, 1) as user_id, name, job_type, parameters, schedule, version,
    created_at, modified_at FROM arbiter_data.scheduled_jobs;


GRANT SELECT ON arbiter_data.scheduled_jobs TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_jobs TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_jobs TO 'frameworkadmin'@'%';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_jobs TO 'job_executor'@'%';


CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_job (IN jobid CHAR(36))
COMMENT 'Delete a job'
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    SET binid = UUID_TO_BIN(jobid, 1);
    IF EXISTS(SELECT 1 FROM arbiter_data.scheduled_jobs WHERE id = binid) THEN
        DELETE FROM arbiter_data.scheduled_jobs WHERE id = UUID_TO_BIN(jobid, 1);
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Job does not exist',
        MYSQL_ERRNO = 1305;
    END IF;
END;

GRANT DELETE, SELECT(id) ON arbiter_data.scheduled_jobs TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_job TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_job TO 'frameworkadmin'@'%';


INSERT INTO scheduled_jobs (id, organization_id, user_id, name, job_type, parameters, schedule, version) VALUES (
   UUID_TO_BIN('907a9340-0b11-11ea-9e88-f4939feddd82', 1),
   UUID_TO_BIN('b76ab62e-4fe1-11e9-9e44-64006a511e6f', 1),
   UUID_TO_BIN('0c90950a-7cca-11e9-a81f-54bf64606445', 1),
   'Test Job',
   'daily_observation_validation', '{"start_td": "-1d", "end_td": "0h", "base_url": "http://localhost:5000"}',
   '{"type": "cron", "cron_string": "0 0 * * *"}',
   0);
