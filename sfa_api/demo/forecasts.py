import datetime as dt


static_forecasts = {
    '11c20780-76ae-4b11-bef1-7a75bdc784e3': {
        "forecast_id": "11c20780-76ae-4b11-bef1-7a75bdc784e3",
        "name": "DA GHI",
        "provider": "Provider A",
        "site_id": "123e4567-e89b-12d3-a456-426655440001",
        "variable": "ghi",
        "issue_time_of_day": "06:00",
        "interval_length": 5,
        "run_length": 1440,
        "interval_label": "beginning",
        "lead_time_to_start": "60",
        "interval_value_type": "interval_mean",
        "created_at": dt.datetime(2019, 3, 1, 11, 55, 37),
        "modified_at": dt.datetime(2019, 3, 1, 11, 55, 37)
    },
    'f8dd49fa-23e2-48a0-862b-ba0af6dec276': {
        "forecast_id": "f8dd49fa-23e2-48a0-862b-ba0af6dec276",
        "name": "HA Power",
        "provider": "Provider A",
        "site_id": "123e4567-e89b-12d3-a456-426655440002",
        "variable": "ac_power",
        "issue_time_of_day": "12:00",
        "run_length": 60,
        "interval_length": 1,
        "interval_label": "beginning",
        "lead_time_to_start": 60,
        "interval_value_type": "interval_mean",
        "created_at": dt.datetime(2019, 3, 1, 11, 55, 38),
        "modified_at": dt.datetime(2019, 3, 1, 11, 55, 38)
    }
}
