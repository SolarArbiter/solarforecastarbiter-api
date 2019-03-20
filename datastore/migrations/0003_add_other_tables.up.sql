-- Create the sites table
CREATE TABLE arbiter_data.sites (
    id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
    organization_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,
    latitude DECIMAL(8, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    elevation DECIMAL(7, 2) NOT NULL,
    timezone VARCHAR(32) NOT NULL,
    extra_parameters VARCHAR(255) NOT NULL,
    ac_capacity DECIMAL(10, 5) NOT NULL,
    dc_capacity DECIMAL(10, 5) NOT NULL,
    temperature_coefficient DECIMAL(7, 5) NOT NULL,
    tracking_type ENUM('fixed', 'single_axis') NOT NULL,
    surface_tilt DECIMAL(4, 2),
    surface_azimuth DECIMAL(5, 2),
    axis_tilt DECIMAL(4, 2),
    axis_azimuth DECIMAL(5, 2),
    ground_coverage_ratio DECIMAL(8, 4),
    backtrack BOOLEAN,
    max_rotation_angle DECIMAL(5, 2),
    irradiance_loss_factor DECIMAL(5, 2) NOT NULL,
    dc_loss_factor DECIMAL(5, 2) NOT NULL,
    ac_loss_factor DECIMAL(5, 2) NOT NULL,

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
    value_type VARCHAR(32) NOT NULL,
    uncertainty FLOAT NOT NULL,
    extra_parameters VARCHAR(255) NOT NULL,

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
CREATE TABLE arbiter_data.forecasts(
    id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID(), 1)),
    organization_id BINARY(16) NOT NULL,
    site_id BINARY(16) NOT NULL,
    name VARCHAR(64) NOT NULL,
    variable VARCHAR(32) NOT NULL,
    issue_time_of_day TIME NOT NULL,
    lead_time_to_start SMALLINT UNSIGNED NOT NULL,
    interval_label ENUM('beginning', 'ending', 'instant') NOT NULL,
    interval_length SMALLINT UNSIGNED NOT NULL,
    run_length SMALLINT UNSIGNED NOT NULL,
    value_type VARCHAR(32) NOT NULL,
    extra_parameters VARCHAR(255) NOT NULL,

    PRIMARY KEY (id),
    KEY (site_id),
    FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    FOREIGN KEY (site_id)
        REFERENCES sites(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
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
