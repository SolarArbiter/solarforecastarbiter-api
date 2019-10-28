import datetime as dt


ca = dt.datetime(2019, 9, 25, 0, 0, tzinfo=dt.timezone.utc)
ef = dt.datetime(2019, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
static_aggregates = {
    "458ffc27-df0b-11e9-b622-62adb5fd6af0": {
        "aggregate_id": "458ffc27-df0b-11e9-b622-62adb5fd6af0",
        "name": "Test Aggregate ghi",
        "provider": "Organization 1",
        "variable": "ghi",
        "interval_label": "ending",
        "interval_length": 60,
        "interval_value_type": "interval_mean",
        "aggregate_type": "mean",
        "extra_parameters": "extra",
        "description": "ghi agg",
        "timezone": "America/Denver",
        "created_at": dt.datetime(2019, 9, 24, 12, 0, tzinfo=dt.timezone.utc),
        "modified_at": dt.datetime(2019, 9, 24, 12, 0, tzinfo=dt.timezone.utc),
        "observations": [
            {"observation_id": "123e4567-e89b-12d3-a456-426655440000",
             "created_at": ca,
             "effective_from": ef,
             "observation_deleted_at": None,
             "effective_until": None},
            {"observation_id": "e0da0dea-9482-4073-84de-f1b12c304d23",
             "created_at": ca,
             "effective_from": ef,
             "observation_deleted_at": None,
             "effective_until": None},
            {"observation_id": "b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2",
             "created_at": ca,
             "effective_from": ef,
             "observation_deleted_at": None,
             "effective_until": None},
        ]
    },
    "d3d1e8e5-df1b-11e9-b622-62adb5fd6af0": {
        "aggregate_id": "d3d1e8e5-df1b-11e9-b622-62adb5fd6af0",
        "name": "Test Aggregate dni",
        "provider": "Organization 1",
        "variable": "dni",
        "interval_label": "ending",
        "interval_length": 60,
        "interval_value_type": "interval_mean",
        "aggregate_type": "mean",
        "extra_parameters": "extra",
        "description": "dni agg",
        "timezone": "America/Denver",
        "created_at": dt.datetime(2019, 9, 24, 12, 0, tzinfo=dt.timezone.utc),
        "modified_at": dt.datetime(2019, 9, 24, 12, 0, tzinfo=dt.timezone.utc),
        "observations": [
            {"observation_id": "95890740-824f-11e9-a81f-54bf64606445",
             "created_at": ca,
             "observation_deleted_at": None,
             "effective_from": ef,
             "effective_until": None},
            {"observation_id": "9ce9715c-bd91-47b7-989f-50bb558f1eb9",
             "created_at": ca,
             "observation_deleted_at": None,
             "effective_from": ef,
             "effective_until": None}
        ]
    }
}
