import datetime as dt


static_sites = {
    '123e4567-e89b-12d3-a456-426655440001': {
        "elevation": 595.0,
        "extra_parameters": (
            '{"network_api_abbreviation": "AS","network": "University of Oregon SRML","network_api_id": "94040"}' # NOQA
        ),
        "latitude": 42.19,
        "longitude": -122.7,
        "modeling_parameters": {
            "ac_capacity": None,
            "ac_loss_factor": None,
            "axis_azimuth": None,
            "axis_tilt": None,
            "backtrack": None,
            "dc_capacity": None,
            "dc_loss_factor": None,
            "ground_coverage_ratio": None,
            "max_rotation_angle": None,
            "surface_azimuth": None,
            "surface_tilt": None,
            "temperature_coefficient": None,
            "tracking_type": None
        },
        "name": "Weather Station",
        "provider": "Organization 1",
        "timezone": "Etc/GMT+8",
        "site_id": '123e4567-e89b-12d3-a456-426655440001',
        "created_at": dt.datetime(2019, 3, 1, 11, 44, 38),
        "modified_at": dt.datetime(2019, 3, 1, 11, 44, 38)
    },
    'd2018f1d-82b1-422a-8ec4-4e8b3fe92a4a': {
        "elevation": 786.0,
        "extra_parameters": '{"network": "NREL MIDC"}',
        "latitude": 32.22969,
        "longitude": -110.95534,
        "modeling_parameters": {
            "ac_capacity": None,
            "ac_loss_factor": None,
            "axis_azimuth": None,
            "axis_tilt": None,
            "backtrack": None,
            "dc_capacity": None,
            "dc_loss_factor": None,
            "ground_coverage_ratio": None,
            "max_rotation_angle": None,
            "surface_azimuth": None,
            "surface_tilt": None,
            "temperature_coefficient": None,
            "tracking_type": None
        },
        "name": "Weather Station 1",
        "provider": "Organization 1",
        "timezone": "America/Phoenix",
        "site_id": 'd2018f1d-82b1-422a-8ec4-4e8b3fe92a4a',
        "created_at": dt.datetime(2019, 3, 1, 11, 44, 44),
        "modified_at": dt.datetime(2019, 3, 1, 11, 44, 44)
    },
    '123e4567-e89b-12d3-a456-426655440002': {
        "elevation": 786.0,
        "extra_parameters": "",
        "latitude": 43.73403,
        "longitude": -96.62328,
        "modeling_parameters": {
            "ac_capacity": 0.015,
            "ac_loss_factor": 0.0,
            "axis_azimuth": None,
            "axis_tilt": None,
            "backtrack": None,
            "dc_capacity": 0.015,
            "dc_loss_factor": 0.0,
            "ground_coverage_ratio": None,
            "max_rotation_angle": None,
            "surface_azimuth": 180.0,
            "surface_tilt": 45.0,
            "temperature_coefficient": -.002,
            "tracking_type": "fixed"
        },
        "name": "Power Plant 1",
        "provider": "Organization 1",
        "timezone": "Etc/GMT+6",
        "site_id": '123e4567-e89b-12d3-a456-426655440002',
        "created_at": dt.datetime(2019, 3, 1, 11, 44, 46),
        "modified_at": dt.datetime(2019, 3, 1, 11, 44, 46)
    }
}
