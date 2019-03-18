-- Create the sites table
CREATE TABLE arbiter_data.sites (
    id BINARY(16) NOT NULL,
    organization_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,
    -- add everything else later...

    PRIMARY KEY (id),
    FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


-- Create the observations table
CREATE TABLE arbiter_data.observations (
    id BINARY(16) NOT NULL,
    organization_id BINARY(16) NOT NULL,
    site_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,

    -- add everything else later...

    PRIMARY KEY (id),
    KEY (site_id),
    FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    FOREIGN KEY (site_id)
        REFERENCES sites(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


-- Create the forecasts table
-- need to trigger site failure on deletion if forecast exists
CREATE TABLE arbiter_data.forecasts(
    id BINARY(16) NOT NULL,
    organization_id BINARY(16) NOT NULL,
    site_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,

    -- add everything else later...

    PRIMARY KEY (id),
    KEY (site_id),
    FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


-- create the aggregates table
CREATE TABLE arbiter_data.aggregates(
    id BINARY(16) NOT NULL,
    organization_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,

    -- add everything else later...

    PRIMARY KEY (id),
    FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;
