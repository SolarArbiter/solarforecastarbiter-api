import datetime as dt


static_cdf_forecasts = {
    '633f9396-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633f9396-50bb-11e9-8647-d663bd873d93',
        "constant_value": 5.0,
        "parent": 'ef51e87c-50b9-11e9-8647-d663bd873d93',
    },
    '633f9864-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633f9864-50bb-11e9-8647-d663bd873d93',
        "constant_value": 20.0,
        "parent": 'ef51e87c-50b9-11e9-8647-d663bd873d93',
    },
    '633f9b2a-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633f9b2a-50bb-11e9-8647-d663bd873d93',
        "constant_value": 50.0,
        "parent": 'ef51e87c-50b9-11e9-8647-d663bd873d93',
    },
    '633f9d96-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633f9d96-50bb-11e9-8647-d663bd873d93',
        "constant_value": 80.0,
        "parent": 'ef51e87c-50b9-11e9-8647-d663bd873d93',
    },
    '633fa548-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fa548-50bb-11e9-8647-d663bd873d93',
        "constant_value": 95.0,
        "parent": 'ef51e87c-50b9-11e9-8647-d663bd873d93',
    },
    '633fa94e-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fa94e-50bb-11e9-8647-d663bd873d93',
        "constant_value": 0.0,
        "parent": '058b182a-50ba-11e9-8647-d663bd873d93',
    },
    '633fabec-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fabec-50bb-11e9-8647-d663bd873d93',
        "constant_value": 5.0,
        "parent": '058b182a-50ba-11e9-8647-d663bd873d93',

    },
    '633fae62-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fae62-50bb-11e9-8647-d663bd873d93',
        "constant_value": 10.0,
        "parent": '058b182a-50ba-11e9-8647-d663bd873d93',
    },
    '633fb114-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fb114-50bb-11e9-8647-d663bd873d93',
        "constant_value": 15.0,
        "parent": '058b182a-50ba-11e9-8647-d663bd873d93',
    },
    '633fb3a8-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fb3a8-50bb-11e9-8647-d663bd873d93',
        "constant_value": 20.0,
        "parent": '058b182a-50ba-11e9-8647-d663bd873d93',
    },
}
static_cdf_forecast_groups = {
    'ef51e87c-50b9-11e9-8647-d663bd873d93': {
        "forecast_id": "ef51e87c-50b9-11e9-8647-d663bd873d93",
        "name": "DA GHI",
        "extra_parameters": "",
        "provider": "Reference",
        "site_id": "123e4567-e89b-12d3-a456-426655440001",
        "variable": "ghi",
        "issue_time_of_day": "06:00",
        "interval_length": 5,
        "run_length": 1440,
        "interval_label": "beginning",
        "lead_time_to_start": 60,
        "interval_value_type": "interval_mean",
        "axis": "y",
        "constant_values": [
            static_cdf_forecasts['633f9396-50bb-11e9-8647-d663bd873d93'],
            static_cdf_forecasts['633f9864-50bb-11e9-8647-d663bd873d93'],
            static_cdf_forecasts['633f9b2a-50bb-11e9-8647-d663bd873d93'],
            static_cdf_forecasts['633f9d96-50bb-11e9-8647-d663bd873d93'],
            static_cdf_forecasts['633fa548-50bb-11e9-8647-d663bd873d93']],
        "created_at": dt.datetime(2019, 3, 2, 14, 55, 37),
        "modified_at": dt.datetime(2019, 3, 2, 14, 55, 37)
    },
    '058b182a-50ba-11e9-8647-d663bd873d93': {
        "forecast_id": "058b182a-50ba-11e9-8647-d663bd873d93",
        "name": "HA Power",
        "extra_parameters": "",
        "provider": "Reference",
        "site_id": "123e4567-e89b-12d3-a456-426655440002",
        "variable": "ac_power",
        "issue_time_of_day": "12:00",
        "run_length": 60,
        "interval_length": 1,
        "interval_label": "beginning",
        "lead_time_to_start": 60,
        "interval_value_type": "interval_mean",
        "axis": "x",
        "constant_values": [
            static_cdf_forecasts['633fb3a8-50bb-11e9-8647-d663bd873d93'],
            static_cdf_forecasts['633fb114-50bb-11e9-8647-d663bd873d93'],
            static_cdf_forecasts['633fae62-50bb-11e9-8647-d663bd873d93'],
            static_cdf_forecasts['633fabec-50bb-11e9-8647-d663bd873d93'],
            static_cdf_forecasts['633fa94e-50bb-11e9-8647-d663bd873d93']],
        "created_at": dt.datetime(2019, 3, 2, 14, 55, 38),
        "modified_at": dt.datetime(2019, 3, 2, 14, 55, 38)
    }
}
