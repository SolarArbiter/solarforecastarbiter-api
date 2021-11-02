-- Table to store one-off single values e.g. last connection time
-- CREATE TABLE arbiter_data.system_stats(
--     stat_name VARCHAR(32) NOT NULL,
--     stat_value VARCHAR(32)
--     
-- )ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

-- GRANT SELECT ON arbiter_data.system_stats TO 'select_objects'@'localhost';
-- GRANT INSERT ON arbiter_data.system_stats TO 'insert_objects'@'localhost';
-- GRANT UPDATE ON arbiter_data.system_stats TO 'update_objects'@'localhost';
-- GRANT DELETE ON arbiter_data.system_stats TO 'delete_objects'@'localhost';


-- Table for storing system outage information with start, end information
CREATE TABLE arbiter_data.system_outages(
    id BINARY(16) NOT NULL DEFAULT(UUID_TO_BIN(UUID(), 1)),
    start TIMESTAMP NOT NULL,
    end TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY(id)
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

GRANT SELECT ON arbiter_data.system_outages TO 'select_objects'@'localhost';
GRANT INSERT ON arbiter_data.system_outages TO 'insert_objects'@'localhost';
GRANT SELECT, DELETE ON arbiter_data.system_outages TO 'delete_objects'@'localhost';


-- Table for storing report-specific outage with start, end information
CREATE TABLE arbiter_data.report_outages(
    id BINARY(16) NOT NULL DEFAULT(UUID_TO_BIN(UUID(), 1)),
    report_id BINARY(16) NOT NULL,
    start TIMESTAMP NOT NULL,
    end TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY(id),
    FOREIGN KEY (report_id)
        REFERENCES reports(id)
        ON DELETE CASCADE
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;

GRANT SELECT ON arbiter_data.report_outages TO 'select_objects'@'localhost';
GRANT INSERT ON arbiter_data.report_outages TO 'insert_objects'@'localhost';
GRANT SELECT, DELETE ON arbiter_data.report_outages TO 'delete_objects'@'localhost';


-- System outage procedures
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_system_outage (
    IN strid VARCHAR(36), IN start TIMESTAMP, IN end TIMESTAMP)
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    INSERT INTO arbiter_data.system_outages(id, start, end) VALUES (
        binid, start, end
    );
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.store_system_outage TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_system_outage TO 'frameworkadmin'@'%';

CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_system_outages ()
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    SELECT BIN_TO_UUID(id, 1) as outage_id, start, end, created_at, modified_at
    FROM arbiter_data.system_outages;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.list_system_outages TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_system_outages TO 'frameworkadmin'@'%';
-- only allow reading by apiuser on list_system_outages
GRANT EXECUTE ON PROCEDURE arbiter_data.list_system_outages TO 'apiuser'@'%';

CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE read_system_outage(
    In strid VARCHAR(36))
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    SELECT BIN_TO_UUID(id, 1) as outage_id, start, end, created_at, modified_at
        FROM arbiter_data.system_outages
        WHERE id = binid;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.read_system_outage TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.read_system_outage TO 'frameworkadmin'@'%';

CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_system_outage(
    In strid VARCHAR(36))
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE binid BINARY(16);
    SET binid = (SELECT UUID_TO_BIN(strid, 1));
    DELETE FROM arbiter_data.system_outages WHERE id = binid;
END;


GRANT EXECUTE ON PROCEDURE arbiter_data.delete_system_outage TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_system_outage TO 'frameworkadmin'@'%';


-- Report outage procedure
CREATE DEFINER = 'insert_objects'@'localhost' PROCEDURE store_report_outage (
    IN auth0id VARCHAR(32), IN str_reportid VARCHAR(36),
    IN str_outageid VARCHAR(36), IN start TIMESTAMP, IN end TIMESTAMP
)
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE bin_reportid BINARY(16);
    DECLARE bin_outageid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;

    SET bin_reportid = (SELECT UUID_TO_BIN(str_reportid, 1));
    SET bin_outageid = (SELECT UUID_TO_BIN(str_outageid, 1));

    -- Check that the user has update permissions
    SET allowed = (SELECT can_user_perform_action(auth0id, bin_reportid, 'update'));
    IF allowed THEN
        INSERT INTO arbiter_data.report_outages(
            id, report_id, start, end
        ) VALUES (
            bin_outageid, bin_reportid, start, end
        );
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "update report for report outage write"',
        MYSQL_ERRNO = 1142;
    END IF;
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.store_report_outage TO 'insert_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.store_report_outage TO 'apiuser'@'%';

CREATE DEFINER = 'select_objects'@'localhost' PROCEDURE list_report_outages (
    IN auth0id VARCHAR(32), IN str_reportid VARCHAR(36)
)
READS SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE bin_reportid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;

    SET bin_reportid = (SELECT UUID_TO_BIN(str_reportid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, bin_reportid, 'read'));

    IF allowed THEN
        SELECT BIN_TO_UUID(id, 1) as outage_id, BIN_TO_UUID(report_id, 1) as report_id, start, end, created_at, modified_at
        FROM arbiter_data.report_outages
        WHERE report_id = bin_reportid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "read report outages"',
        MYSQL_ERRNO = 1142;
    END IF;
    
END;

GRANT EXECUTE ON PROCEDURE arbiter_data.list_report_outages TO 'select_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.list_report_outages TO 'apiuser'@'%';

CREATE DEFINER = 'delete_objects'@'localhost' PROCEDURE delete_report_outage(
    IN auth0id VARCHAR(32), IN str_reportid VARCHAR(36), IN str_outageid VARCHAR(36)
)
MODIFIES SQL DATA SQL SECURITY DEFINER
BEGIN
    DECLARE bin_reportid BINARY(16);
    DECLARE bin_outageid BINARY(16);
    DECLARE allowed BOOLEAN DEFAULT FALSE;

    SET bin_reportid = (SELECT UUID_TO_BIN(str_reportid, 1));
    SET bin_outageid = (SELECT UUID_TO_BIN(str_outageid, 1));
    SET allowed = (SELECT can_user_perform_action(auth0id, bin_reportid, 'update'));
    
    IF allowed THEN
        DELETE FROM arbiter_data.report_outages WHERE id = bin_outageid;
    ELSE
        SIGNAL SQLSTATE '42000' SET MESSAGE_TEXT = 'Access denied to user on "update report for report outage delete"',
        MYSQL_ERRNO = 1142;
    END IF;
END;


GRANT EXECUTE ON PROCEDURE arbiter_data.delete_report_outage TO 'delete_objects'@'localhost';
GRANT EXECUTE ON PROCEDURE arbiter_data.delete_report_outage TO 'apiuser'@'%';
