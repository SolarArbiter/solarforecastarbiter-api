import datetime as dt
import pytz


static_observations = {
    "123e4567-e89b-12d3-a456-426655440000": {
        "extra_parameters": (
            '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer",'  # NOQA
            ' "network": "UO SRML"}'
        ),
        "name": "GHI Instrument 1",
        "observation_id": "123e4567-e89b-12d3-a456-426655440000",
        "provider": "Organization 1",
        "site_id": "123e4567-e89b-12d3-a456-426655440001",
        "variable": "ghi",
        "interval_value_type": "interval_mean",
        "interval_label": "beginning",
        "interval_length": 5,
        "uncertainty": 0.10,
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 39)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 39))
    },
    "9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f": {
        "extra_parameters": (
            '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer",'  # NOQA
            ' "network": "UO SRML"}'
        ),
        "name": "DHI Instrument 1",
        "observation_id": "9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f",
        "provider": "Organization 1",
        "site_id": "123e4567-e89b-12d3-a456-426655440001",
        "variable": "dhi",
        "interval_value_type": "interval_mean",
        "interval_label": "beginning",
        "interval_length": 5,
        "uncertainty": 0.10,
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 43)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 43))
    },
    "9ce9715c-bd91-47b7-989f-50bb558f1eb9": {
        "extra_parameters": (
            '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer",' # NOQA
            ' "network": "UO SRML"}'
        ),
        "name": "DNI Instrument 2",
        "observation_id": "9ce9715c-bd91-47b7-989f-50bb558f1eb9",
        "provider": "Organization 1",
        "site_id": "123e4567-e89b-12d3-a456-426655440001",
        "variable": "dni",
        "interval_value_type": "interval_mean",
        "interval_label": "beginning",
        "interval_length": 5,
        "uncertainty": 0.10,
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 48)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 48))
    },
    "e0da0dea-9482-4073-84de-f1b12c304d23": {
        "extra_parameters": (
            '{"instrument": "Kipp & Zonen CMP 22 Pyranometer",'
            ' "network": "UO SRML"}'
        ),
        "name": "GHI Instrument 2",
        "observation_id": "e0da0dea-9482-4073-84de-f1b12c304d23",
        "provider": "Organization 1",
        "site_id": "d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a",
        "variable": "ghi",
        "interval_value_type": "interval_mean",
        "interval_label": "beginning",
        "interval_length": 5,
        "uncertainty": 0.10,
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 55)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 55))
    },
    "b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2": {
        "extra_parameters": (
            '{"instrument": "Kipp & Zonen CMP 22 Pyranometer",'
            ' "network": "NOAA"}'
        ),
        "name": "Sioux Falls, ghi",
        "observation_id": "b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2",
        "provider": "Organization 1",
        "site_id": "d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a",
        "variable": "ghi",
        "interval_value_type": "interval_mean",
        "interval_label": "beginning",
        "interval_length": 5,
        "uncertainty": 0.10,
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 2, 38)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 2, 38))
    }
}
