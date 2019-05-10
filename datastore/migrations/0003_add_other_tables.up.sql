-- Create the sites table
CREATE TABLE arbiter_data.sites (
    id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
    organization_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,
    latitude DECIMAL(8, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    elevation DECIMAL(7, 2) NOT NULL,
    timezone VARCHAR(32) NOT NULL,
    extra_parameters TEXT NOT NULL,  -- unclear if this will have a positive or negative effect on performance
    ac_capacity DECIMAL(10, 6),
    dc_capacity DECIMAL(10, 6),
    temperature_coefficient DECIMAL(7, 5),
    tracking_type ENUM('fixed', 'single_axis'),
    surface_tilt DECIMAL(4, 2),
    surface_azimuth DECIMAL(5, 2),
    axis_tilt DECIMAL(4, 2),
    axis_azimuth DECIMAL(5, 2),
    ground_coverage_ratio DECIMAL(8, 4),
    backtrack BOOLEAN,
    max_rotation_angle DECIMAL(5, 2),
    dc_loss_factor DECIMAL(5, 2),
    ac_loss_factor DECIMAL(5, 2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


-- Create the observations table
CREATE TABLE arbiter_data.observations (
    id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
    organization_id BINARY(16) NOT NULL,
    site_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,
    variable VARCHAR(32) NOT NULL,
    interval_label ENUM('beginning', 'ending', 'instant') NOT NULL,
    interval_length SMALLINT UNSIGNED NOT NULL,
    interval_value_type VARCHAR(32) NOT NULL,
    uncertainty FLOAT NOT NULL,
    extra_parameters TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY (site_id),
    FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    FOREIGN KEY (site_id)
        REFERENCES sites(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


-- create the table to hold values for observations
CREATE TABLE arbiter_data.observations_values (
    id BINARY(16) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    value FLOAT NOT NULL,
    quality_flag SMALLINT UNSIGNED NOT NULL,

    PRIMARY KEY (id, timestamp),
    FOREIGN KEY (id)
        REFERENCES observations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


-- Create the forecasts table
CREATE TABLE arbiter_data.forecasts(
    id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
    organization_id BINARY(16) NOT NULL,
    site_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,
    variable VARCHAR(32) NOT NULL,
    issue_time_of_day VARCHAR(5) NOT NULL,
    lead_time_to_start SMALLINT UNSIGNED NOT NULL,
    interval_label ENUM('beginning', 'ending', 'instant') NOT NULL,
    interval_length SMALLINT UNSIGNED NOT NULL,
    run_length SMALLINT UNSIGNED NOT NULL,
    interval_value_type VARCHAR(32) NOT NULL,
    extra_parameters TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY (site_id),
    FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    FOREIGN KEY (site_id)
        REFERENCES sites(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


-- create the table to hold values for forecasts
CREATE TABLE arbiter_data.forecasts_values (
    id BINARY(16) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    value FLOAT NOT NULL,

    PRIMARY KEY (id, timestamp),
    FOREIGN KEY (id)
        REFERENCES forecasts(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;


-- create the aggregates table
CREATE TABLE arbiter_data.aggregates(
    id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
    organization_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,

    -- add everything else later...

    PRIMARY KEY (id),
    FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=INNODB ENCRYPTION='Y' ROW_FORMAT=COMPRESSED;
