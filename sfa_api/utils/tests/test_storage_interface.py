import datetime as dt
import json
import math
import uuid


from cryptography.fernet import Fernet
import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest
import pymysql


from sfa_api import create_app
from sfa_api.conftest import (
    demo_sites, demo_observations, demo_forecasts, demo_single_cdf,
    demo_group_cdf, demo_aggregates, generate_randoms, _make_nocommit_cursor)
from sfa_api.utils import storage_interface


TESTINDICES = {
    1: generate_randoms(1)[0].to_series(),
    5: generate_randoms(5)[0].to_series(),
    60: generate_randoms(60)[0].to_series(),
}


def remove_reference(obj_list):
    return [obj for obj in obj_list
            if obj['provider'] != 'Reference']


@pytest.fixture(params=[0, 1, 2, 3, 4])
def startend(request):
    if request.param == 0:
        start = None
        end = None
    elif request.param == 1:
        start = pd.Timestamp('20190414T1205Z')
        end = None
    elif request.param == 2:
        start = None
        end = pd.Timestamp('20190414T1215Z')
    elif request.param == 3:
        start = pd.Timestamp('20190414T1205Z')
        end = pd.Timestamp('20190414T1215Z')
    else:
        start = pd.Timestamp('20190414T0505-0700')
        end = pd.Timestamp('20190414T1015-0200')
    return start, end


def convert_startend(start, end):
    if start is not None:
        utc_start = start.tz_convert('utc')
    else:
        utc_start = None
    if end is not None:
        utc_end = end.tz_convert('utc')
    else:
        utc_end = None
    return utc_start, utc_end


def test_escape_float_with_nan():
    assert storage_interface.escape_float_with_nan(math.nan) == 'NULL'
    assert storage_interface.escape_float_with_nan(np.nan) == 'NULL'
    assert storage_interface.escape_float_with_nan(0.9) == '0.9'


def test_escape_timestamp():
    assert storage_interface.escape_timestamp(
        pd.Timestamp('2019-04-08T030423')) == "'2019-04-08 03:04:23'"
    assert storage_interface.escape_timestamp(
        pd.Timestamp('2019-04-08T030423Z')) == "'2019-04-08 03:04:23'"
    assert storage_interface.escape_timestamp(
        pd.Timestamp('2019-04-08T030423-0300')) == "'2019-04-08 06:04:23'"


def test_escape_datetime():
    assert storage_interface.escape_datetime(
        dt.datetime(2019, 5, 1, 23, 33, 12)) == "'2019-05-01 23:33:12'"
    assert (storage_interface.escape_datetime(
        dt.datetime(2019, 5, 1, 23, 33, 12,
                    tzinfo=dt.timezone(dt.timedelta(hours=-5)))) ==
            "'2019-05-02 04:33:12'")


def test_convert_datetime_utc():
    assert (
        storage_interface.convert_datetime_utc('2019-05-01 23:01:32') ==
        dt.datetime(2019, 5, 1, 23, 1, 32,
                    tzinfo=dt.timezone(dt.timedelta(hours=0))))


def test_try_query_raises():
    with pytest.raises(pymysql.err.IntegrityError):
        def f():
            raise pymysql.err.IntegrityError(1001)
        storage_interface.try_query(f)


def test_get_cursor_and_timezone(sql_app):
    with storage_interface.get_cursor('standard') as cursor:
        cursor.execute('SELECT @@session.time_zone')
        res = cursor.fetchone()[0]
    assert res == '+00:00'


def test_get_cursor_invalid_type(sql_app):
    with pytest.raises(AttributeError):
        with storage_interface.get_cursor('oither'): pass  # NOQA


def test_cursor_rollback(sql_app, user):
    obs_id = list(demo_observations.keys())[0]
    with pytest.raises(ValueError):
        with storage_interface.get_cursor('standard') as cursor:
            cursor.execute('CALL delete_observation(%s, %s)',
                           (storage_interface.current_user, obs_id))
            raise ValueError
    res = storage_interface.read_observation(obs_id)
    assert res == demo_observations[obs_id]


def test_cursor_rollback_internal_err(sql_app):
    obs_id = list(demo_observations.keys())[0]
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_observation(obs_id)

    ctx = sql_app.test_request_context()
    ctx.user = 'auth0|5be343df7025406237820b85'
    ctx.push()
    res = storage_interface.read_observation(obs_id)
    assert res == demo_observations[obs_id]
    ctx.pop()


def test_cursor_commit(sql_app, user):
    demo = list(demo_observations.values())[0].copy()
    demo['name'] = 'demo'
    new_id = storage_interface.store_observation(demo)
    storage_interface.delete_observation(new_id)
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation(new_id)


def test_list_observations(sql_app, user):
    observations = storage_interface.list_observations()
    for obs in remove_reference(observations):
        assert obs == demo_observations[obs['observation_id']]


def test_list_observations_invalid_user(sql_app, invalid_user):
    observations = storage_interface.list_observations()
    assert len(observations) == 0


def test_list_observations_invalid_site(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.list_observations(str(uuid.uuid1()))


@pytest.mark.parametrize('observation_id', demo_observations.keys())
def test_read_observation(sql_app, user, observation_id):
    observation = storage_interface.read_observation(observation_id)
    assert observation == demo_observations[observation_id]


def test_read_observation_invalid_observation(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation(str(uuid.uuid1()))


def test_read_observation_not_uuid(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError) as err:
        storage_interface.read_observation('f8dd49fa-23e2-48a0-862b-ba0af6de')
    assert "Incorrect string value" in str(err.value)


def test_read_observation_invalid_user(sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation(list(demo_observations.keys())[0])


@pytest.mark.parametrize('observation_id', demo_observations.keys())
def test_read_observation_values(sql_app, user, observation_id, startend):
    idx_step = demo_observations[observation_id]['interval_length']
    start, end = startend
    observation_values = storage_interface.read_observation_values(
        observation_id, start, end)
    obs_index = observation_values.index
    utc_start, utc_end = convert_startend(start, end)
    assert (obs_index == TESTINDICES[idx_step].loc[utc_start:utc_end].index).all() # NOQA
    assert (observation_values.columns == ['value', 'quality_flag']).all()


def test_read_observation_values_invalid_observation(sql_app, user, startend):
    start, end = startend
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation_values(
            str(uuid.uuid1()), start, end)


def test_read_observation_values_invalid_user(sql_app, invalid_user, startend):
    start, end = startend
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation_values(
            list(demo_observations.keys())[0], start, end)


@pytest.mark.parametrize('observation_id', demo_observations.keys())
def test_read_latest_observation_value(sql_app, user, observation_id):
    idx_step = demo_observations[observation_id]['interval_length']
    observation_values = storage_interface.read_latest_observation_value(
        observation_id)
    fx_index = observation_values.index
    assert len(fx_index) == 1
    assert fx_index[0] == TESTINDICES[idx_step].index[-1]
    assert (observation_values.columns == ['value', 'quality_flag']).all()


def test_read_latest_observation_value_no_data(sql_app, user, nocommit_cursor):
    observation = list(demo_observations.values())[0].copy()
    observation['name'] = 'new_observation'
    new_id = storage_interface.store_observation(observation)
    observation_values = storage_interface.read_latest_observation_value(
        new_id)
    obs_index = observation_values.index
    assert len(obs_index) == 0


def test_read_latest_df_observation_value_invalid_observation(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_latest_observation_value(
            str(uuid.uuid1()))


def test_read_latest_observation_value_fx_id(sql_app, user, forecast_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_latest_observation_value(
            forecast_id)


def test_read_latest_observation_value_invalid_user(
        sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation_values(
            list(demo_single_cdf.keys())[0])


@pytest.mark.parametrize('observation_id', demo_observations.keys())
def test_read_observation_time_range(sql_app, user, observation_id):
    idx_step = demo_observations[observation_id]['interval_length']
    trange = storage_interface.read_observation_time_range(
        observation_id)
    assert len(trange) == 2
    assert trange['min_timestamp'] == TESTINDICES[idx_step].index[0]
    assert trange['max_timestamp'] == TESTINDICES[idx_step].index[-1]


def test_read_observation_time_range_no_data(sql_app, user, nocommit_cursor):
    observation = list(demo_observations.values())[0].copy()
    observation['name'] = 'new_observation'
    new_id = storage_interface.store_observation(observation)
    trange = storage_interface.read_observation_time_range(new_id)
    assert len(trange) == 2
    assert trange['min_timestamp'] is None
    assert trange['max_timestamp'] is None


def test_read_observation_time_range_invalid_observation(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation_time_range(
            str(uuid.uuid1()))


def test_read_observation_time_range_invalid_user(
        sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation_time_range(
            list(demo_single_cdf.keys())[0])


@pytest.mark.parametrize('observation', demo_observations.values())
def test_store_observation(sql_app, user, observation, nocommit_cursor):
    observation = observation.copy()
    observation['name'] = 'new_observation'
    new_id = storage_interface.store_observation(observation)
    new_observation = storage_interface.read_observation(new_id)
    observation['observation_id'] = new_id
    for key in ('provider', 'modified_at', 'created_at'):
        del observation[key]
        del new_observation[key]
    assert observation == new_observation


def test_store_observation_none_uncertainty(
        sql_app, user, observation_id, nocommit_cursor):
    observation = demo_observations[observation_id].copy()
    observation['uncertainty'] = None
    observation['name'] = 'new_observation'
    new_id = storage_interface.store_observation(observation)
    new_observation = storage_interface.read_observation(new_id)
    observation['observation_id'] = new_id
    for key in ('provider', 'modified_at', 'created_at'):
        del observation[key]
        del new_observation[key]
    assert observation == new_observation


def test_store_observation_invalid_user(
        sql_app, invalid_user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_observation(
            list(demo_observations.values())[0])


def test_process_df_into_json():
    df = pd.DataFrame({'value': [1.0, 3.0, np.nan]},
                      index=pd.date_range(
                          start='2020-02-02T00:00:00Z',
                          periods=3, freq='10min'))
    out = storage_interface._process_df_into_json(df)
    jo = json.loads(out)
    assert [j['ts'] for j in jo] == [i.strftime('%Y-%m-%dT%H:%M:%S')
                                     for i in df.index]
    assert [j.get('v', 'NO!') for j in jo] == [1.0, 3.0, 'NO!']


def test_process_df_into_json_empty():
    df = pd.DataFrame({'value': []},
                      index=pd.DatetimeIndex([]))
    out = storage_interface._process_df_into_json(df)
    jo = json.loads(out)
    assert len(jo) == 0


def test_process_df_into_json_extended():
    df = pd.DataFrame({'value': [1.0, 3.0, 9.91992993000],
                       'quality_flag': [0, 1, 999]},
                      index=pd.date_range(
                          start='2020-02-02T00:00:00.01299Z',
                          periods=3, freq='10min'))
    out = storage_interface._process_df_into_json(df, 4)
    jo = json.loads(out)
    assert [j['ts'] for j in jo] == [i.strftime('%Y-%m-%dT%H:%M:%S')
                                     for i in df.index]
    assert [j['v'] for j in jo] == [1.0, 3.0, 9.9199]
    assert [j['qf'] for j in jo] == [0, 1, 999]


@pytest.mark.parametrize('observation', demo_observations.values())
def test_store_observation_values(sql_app, user, nocommit_cursor,
                                  observation, obs_vals):
    observation['name'] = 'new_observation'
    new_id = storage_interface.store_observation(observation)
    storage_interface.store_observation_values(new_id, obs_vals)
    stored = storage_interface.read_observation_values(new_id)
    pdt.assert_frame_equal(stored, obs_vals, check_freq=False)


def test_store_observation_values_tz(sql_app, user, nocommit_cursor, obs_vals):
    observation = list(demo_observations.values())[0]
    observation['name'] = 'new_observation'
    new_id = storage_interface.store_observation(observation)
    storage_interface.store_observation_values(
        new_id, obs_vals.tz_convert('MST'))
    stored = storage_interface.read_observation_values(new_id)
    pdt.assert_frame_equal(stored, obs_vals, check_freq=False)


def test_store_observation_values_nan(sql_app, user, nocommit_cursor,
                                      obs_vals):
    observation = list(demo_observations.values())[0]
    observation['name'] = 'new_observation'
    new_id = storage_interface.store_observation(observation)
    obs_vals.loc[2:4, ['value']] = np.nan
    assert np.isnan(obs_vals['value']).sum() > 0
    storage_interface.store_observation_values(new_id, obs_vals)
    stored = storage_interface.read_observation_values(new_id)
    pdt.assert_frame_equal(stored, obs_vals, check_freq=False)


def test_store_observation_values_no_observation(
        sql_app, user, nocommit_cursor, obs_vals):
    new_id = str(uuid.uuid1())
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_observation_values(new_id, obs_vals)


def test_store_observation_values_invalid_user(sql_app, invalid_user,
                                               nocommit_cursor, obs_vals):
    obs_id = list(demo_observations.keys())[0]
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_observation_values(obs_id, obs_vals)


@pytest.mark.parametrize('newparams', [
    {'name': 'updated name'},
    {},
    {'extra_parameters': 'new extra', 'uncertainty': -0.9},
    {'name': 'updated', 'extra_parameters': None},
    {'uncertainty': None, 'name': None},
    {'uncertainty': None, 'null_uncertainty': True}
])
def test_update_observation(sql_app, user, nocommit_cursor,
                            newparams, observation_id):
    observation = storage_interface.read_observation(observation_id)
    storage_interface.update_observation(observation_id, **newparams)
    updated = storage_interface.read_observation(observation_id)
    observation['observation_id'] = observation_id
    observation.update(
        {k: v for k, v in newparams.items()
         if k != 'null_uncertainty' and (v is not None or (
                 k == 'uncertainty' and
                 newparams.get('null_uncertainty', False)))
         })

    assert updated.pop('modified_at') >= observation.pop('modified_at')
    assert updated == observation


def test_update_observation_invalid_user(
        sql_app, invalid_user, nocommit_cursor, observation_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_observation(observation_id, name='new')


def test_update_observation_does_not_exist(
        sql_app, invalid_user, nocommit_cursor, missing_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_observation(missing_id, name='new')


def test_update_observation_is_fx(sql_app, invalid_user, nocommit_cursor,
                                  forecast_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_observation(forecast_id, name='new')


@pytest.mark.parametrize('observation_id', demo_observations.keys())
def test_delete_observation(sql_app, user, nocommit_cursor, observation_id):
    storage_interface.delete_observation(observation_id)
    observation_list = [
        k['observation_id'] for k in storage_interface.list_observations()]
    assert observation_id not in observation_list


def test_delete_observation_invalid_user(
        sql_app, invalid_user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_observation(list(demo_observations.keys())[0])


def test_delete_observation_does_not_exist(sql_app, user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_observation(str(uuid.uuid1()))


def test_list_forecasts(sql_app, user):
    forecasts = storage_interface.list_forecasts()
    for fx in remove_reference(forecasts):
        assert fx == demo_forecasts[fx['forecast_id']]


def test_list_forecasts_invalid_user(sql_app, invalid_user):
    forecasts = storage_interface.list_forecasts()
    assert len(forecasts) == 0


def test_list_forecasts_invalid_site(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.list_forecasts(str(uuid.uuid1()))


@pytest.fixture()
def site_id_with_forecasts(forecast_id):
    return demo_forecasts[forecast_id]['site_id']


def test_list_forecasts_filter_by_site(
        sql_app, user, site_id_with_forecasts):
    forecasts = storage_interface.list_forecasts(
        site_id=site_id_with_forecasts)
    assert len(forecasts) > 0
    for fx in forecasts:
        assert fx['site_id'] == site_id_with_forecasts


def test_list_forecasts_filter_by_aggregate(sql_app, user, aggregate_id):
    forecasts = storage_interface.list_forecasts(aggregate_id=aggregate_id)
    assert len(forecasts) > 0
    for fx in forecasts:
        assert fx['aggregate_id'] == aggregate_id


@pytest.mark.parametrize('forecast_id', demo_forecasts.keys())
def test_read_forecast(sql_app, user, forecast_id):
    forecast = storage_interface.read_forecast(forecast_id)
    assert forecast == demo_forecasts[forecast_id]


def test_read_forecast_invalid_forecast(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_forecast(str(uuid.uuid1()))


def test_read_forecast_invalid_user(sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_forecast(list(demo_forecasts.keys())[0])


@pytest.mark.parametrize('forecast_id', demo_forecasts.keys())
def test_read_forecast_values(sql_app, user, forecast_id, startend):
    idx_step = demo_forecasts[forecast_id]['interval_length']
    start, end = startend
    forecast_values = storage_interface.read_forecast_values(
        forecast_id, start, end)
    fx_index = forecast_values.index
    utc_start, utc_end = convert_startend(start, end)
    assert (fx_index == TESTINDICES[idx_step].loc[utc_start:utc_end].index).all() # NOQA
    assert (forecast_values.columns == ['value']).all()


def test_read_forecast_values_invalid_forecast(sql_app, user, startend):
    start, end = startend
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_forecast_values(
            str(uuid.uuid1()), start, end)


def test_read_forecast_values_invalid_user(sql_app, invalid_user, startend):
    start, end = startend
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_forecast_values(
            list(demo_forecasts.keys())[0], start, end)


@pytest.mark.parametrize('forecast_id', demo_forecasts.keys())
def test_read_latest_forecast_value(sql_app, user, forecast_id):
    idx_step = demo_forecasts[forecast_id]['interval_length']
    forecast_values = storage_interface.read_latest_forecast_value(
        forecast_id)
    fx_index = forecast_values.index
    assert len(fx_index) == 1
    assert fx_index[0] == TESTINDICES[idx_step].index[-1]
    assert (forecast_values.columns == ['value']).all()


def test_read_latest_forecast_value_no_data(sql_app, user, nocommit_cursor):
    forecast = list(demo_forecasts.values())[0].copy()
    forecast['name'] = 'new_forecast'
    new_id = storage_interface.store_forecast(forecast)
    forecast_values = storage_interface.read_latest_forecast_value(new_id)
    fx_index = forecast_values.index
    assert len(fx_index) == 0


def test_read_latest_forecast_value_invalid_forecast(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_latest_forecast_value(
            str(uuid.uuid1()))


def test_read_latest_forecast_value_obs_id(sql_app, user, observation_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_latest_forecast_value(
            observation_id)


def test_read_latest_forecast_value_invalid_user(
        sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_forecast_values(
            list(demo_single_cdf.keys())[0])


@pytest.mark.parametrize('forecast_id', demo_forecasts.keys())
def test_read_forecast_time_range(sql_app, user, forecast_id):
    idx_step = demo_forecasts[forecast_id]['interval_length']
    trange = storage_interface.read_forecast_time_range(
        forecast_id)
    assert len(trange) == 2
    assert trange['min_timestamp'] == TESTINDICES[idx_step].index[0]
    assert trange['max_timestamp'] == TESTINDICES[idx_step].index[-1]


def test_read_forecast_time_range_no_data(sql_app, user, nocommit_cursor):
    forecast = list(demo_forecasts.values())[0].copy()
    forecast['name'] = 'new_forecast'
    new_id = storage_interface.store_forecast(forecast)
    trange = storage_interface.read_forecast_time_range(new_id)
    assert len(trange) == 2
    assert trange['min_timestamp'] is None
    assert trange['max_timestamp'] is None


def test_read_forecast_time_range_invalid_forecast(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_forecast_time_range(
            str(uuid.uuid1()))


def test_read_forecast_time_range_invalid_user(
        sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_forecast_time_range(
            list(demo_single_cdf.keys())[0])


@pytest.mark.parametrize('forecast', demo_forecasts.values())
def test_store_forecast(sql_app, user, forecast, nocommit_cursor):
    forecast = forecast.copy()
    forecast['name'] = 'new_forecast'
    new_id = storage_interface.store_forecast(forecast)
    new_forecast = storage_interface.read_forecast(new_id)
    forecast['forecast_id'] = new_id
    for key in ('provider', 'modified_at', 'created_at'):
        del forecast[key]
        del new_forecast[key]
    assert forecast == new_forecast


def test_store_forecast_invalid_user(sql_app, invalid_user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_forecast(list(demo_forecasts.values())[0])


@pytest.mark.parametrize('forecast', demo_forecasts.values())
def test_store_forecast_values(sql_app, user, nocommit_cursor,
                               forecast, fx_vals):
    forecast['name'] = 'new_forecast'
    new_id = storage_interface.store_forecast(forecast)
    storage_interface.store_forecast_values(new_id, fx_vals)
    stored = storage_interface.read_forecast_values(new_id)
    pdt.assert_frame_equal(stored, fx_vals, check_freq=False)


def test_store_forecast_values_nan(sql_app, user, nocommit_cursor,
                                   fx_vals):
    forecast = list(demo_forecasts.values())[0]
    new_id = storage_interface.store_forecast(forecast)
    fx_vals.loc[2:4, ['value']] = np.nan
    assert np.isnan(fx_vals['value']).sum() > 0
    storage_interface.store_forecast_values(new_id, fx_vals)
    stored = storage_interface.read_forecast_values(new_id)
    pdt.assert_frame_equal(stored, fx_vals, check_freq=False)


def test_store_forecast_values_tz(sql_app, user, nocommit_cursor, fx_vals):
    forecast = list(demo_forecasts.values())[0]
    forecast['name'] = 'new_forecast'
    new_id = storage_interface.store_forecast(forecast)
    storage_interface.store_forecast_values(new_id, fx_vals.tz_convert('MST'))
    stored = storage_interface.read_forecast_values(new_id)
    pdt.assert_frame_equal(stored, fx_vals, check_freq=False)


def test_store_forecast_values_no_forecast(sql_app, user, nocommit_cursor,
                                           fx_vals):
    new_id = str(uuid.uuid1())
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_forecast_values(new_id, fx_vals)


def test_store_forecast_values_invalid_user(sql_app, invalid_user,
                                            nocommit_cursor, fx_vals):
    fx_id = list(demo_forecasts.keys())[0]
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_forecast_values(fx_id, fx_vals)


@pytest.mark.parametrize('newparams', [
    {'name': 'updated name'},
    {},
    {'extra_parameters': 'new extra'},
    {'name': 'updated', 'extra_parameters': None}
])
def test_update_forecast(sql_app, user, nocommit_cursor,
                         newparams, forecast_id):
    forecast = storage_interface.read_forecast(forecast_id)
    storage_interface.update_forecast(forecast_id, **newparams)
    updated = storage_interface.read_forecast(forecast_id)
    forecast['forecast_id'] = forecast_id
    forecast.update({k: v for k, v in newparams.items() if v is not None})
    assert updated.pop('modified_at') >= forecast.pop('modified_at')
    assert updated == forecast


def test_update_forecast_invalid_user(sql_app, invalid_user, nocommit_cursor,
                                      forecast_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_forecast(forecast_id, name='new')


def test_update_forecast_does_not_exist(sql_app, invalid_user, nocommit_cursor,
                                        missing_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_forecast(missing_id, name='new')


def test_update_forecast_access_denied(sql_app, invalid_user, nocommit_cursor,
                                       inaccessible_forecast_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_forecast(inaccessible_forecast_id, name='new')


@pytest.mark.parametrize('forecast_id', demo_forecasts.keys())
def test_delete_forecast(sql_app, user, nocommit_cursor, forecast_id):
    storage_interface.delete_forecast(forecast_id)
    forecast_list = [k['forecast_id']
                     for k in storage_interface.list_forecasts()]
    assert forecast_id not in forecast_list


def test_delete_forecast_invalid_user(sql_app, invalid_user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_forecast(list(demo_forecasts.keys())[0])


def test_delete_forecast_does_not_exist(sql_app, user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_forecast(str(uuid.uuid1()))


@pytest.mark.parametrize('site_id', demo_sites.keys())
def test_read_site(sql_app, user, site_id):
    site = storage_interface.read_site(site_id)
    assert site == demo_sites[site_id]


def test_read_site_invalid_site(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_site(str(uuid.uuid1()))


def test_read_site_invalid_user(sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_site(list(demo_sites.keys())[0])


def test_list_sites(sql_app, user):
    sites = storage_interface.list_sites()
    for site in remove_reference(sites):
        assert site == demo_sites[site['site_id']]


def test_list_sites_invalid_user(sql_app, invalid_user):
    sites = storage_interface.list_sites()
    assert len(sites) == 0


def test_list_sites_in_zone(sql_app, user):
    sites = storage_interface.list_sites_in_zone('Reference Region 3')
    assert len(sites) > 0
    for site in sites:
        assert 'Reference Region 3' in site['climate_zones']


def test_list_sites_in_zone_invalid_user(sql_app, invalid_user):
    sites = storage_interface.list_sites_in_zone('Reference Region 3')
    assert len(sites) == 0


def test_list_sites_in_zone_no_zone(sql_app, invalid_user):
    sites = storage_interface.list_sites_in_zone('Reference Region 11')
    assert len(sites) == 0


@pytest.mark.parametrize('site', demo_sites.values())
def test_store_site(sql_app, user, site, nocommit_cursor):
    site = site.copy()
    site['name'] = 'new_site'
    new_id = storage_interface.store_site(site)
    new_site = storage_interface.read_site(new_id)
    site['site_id'] = new_id
    del site['modified_at']
    del site['created_at']
    del new_site['modified_at']
    del new_site['created_at']
    assert site == new_site


def test_store_site_invalid_user(sql_app, invalid_user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_site(list(demo_sites.values())[0])


_modeling_params = {
    'ac_capacity': None, 'dc_capacity': None, 'temperature_coefficient': None,
    'tracking_type': None, 'surface_tilt': None, 'surface_azimuth': None,
    'axis_tilt': None, 'axis_azimuth': None, 'ground_coverage_ratio': None,
    'backtrack': None, 'max_rotation_angle': None, 'dc_loss_factor': None,
    'ac_loss_factor': None
}


@pytest.mark.parametrize('newparams', [
    {**_modeling_params, 'name': 'updated name'},
    _modeling_params,
    {**_modeling_params, 'extra_parameters': 'new extra'},
    {**_modeling_params, 'name': 'updated', 'extra_parameters': None,
     'ac_capacity': 100},
    {**_modeling_params, 'name': None, 'backtrack': False}
])
def test_update_site(sql_app, user, nocommit_cursor,
                     newparams, site_id):
    site = storage_interface.read_site(site_id)
    storage_interface.update_site(site_id, **newparams)
    updated = storage_interface.read_site(site_id)
    site['site_id'] = site_id
    if newparams.get('name') is not None:
        assert updated['name'] == newparams['name']
    else:
        assert updated['name'] == site['name']
    if newparams.get('extra_parameters') is not None:
        assert updated['extra_parameters'] == newparams['extra_parameters']
    else:
        assert updated['extra_parameters'] == site['extra_parameters']
    for k, v in updated['modeling_parameters'].items():
        if newparams.get(k) is not None:
            assert v == newparams[k]
        else:
            assert v == site['modeling_parameters'][k]


def test_update_site_invalid_user(sql_app, invalid_user, nocommit_cursor,
                                  site_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_site(site_id, name='new',
                                      **_modeling_params)


def test_update_site_does_not_exist(sql_app, invalid_user, nocommit_cursor,
                                    missing_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_site(missing_id, name='new',
                                      **_modeling_params)


def test_update_site_access_is_fx(sql_app, invalid_user, nocommit_cursor,
                                  forecast_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_site(forecast_id, name='new',
                                      **_modeling_params)


@pytest.mark.parametrize('site', demo_sites.values())
def test_delete_site(sql_app, user, nocommit_cursor, site):
    # create a new site to delete since it can be restrict by obs/fx
    site = site.copy()
    site['name'] = 'new_site'
    new_id = storage_interface.store_site(site)
    site_list = [k['site_id'] for k in storage_interface.list_sites()]
    assert new_id in site_list
    storage_interface.delete_site(new_id)
    site_list = [k['site_id'] for k in storage_interface.list_sites()]
    assert new_id not in site_list


def test_delete_site_forecast_restricts(sql_app, user, nocommit_cursor):
    with pytest.raises(storage_interface.DeleteRestrictionError):
        storage_interface.delete_site(list(demo_sites.keys())[0])


def test_delete_site_invalid_user(sql_app, invalid_user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_site(list(demo_sites.keys())[0])


def test_delete_site_does_not_exist(sql_app, user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_site(str(uuid.uuid1()))


# CDF
@pytest.mark.parametrize('forecast_id', demo_single_cdf.keys())
def test_read_cdf_forecast_values(sql_app, user, forecast_id, startend):
    parent_id = demo_single_cdf[forecast_id]['parent']
    idx_step = demo_group_cdf[parent_id]['interval_length']
    start, end = startend
    forecast_values = storage_interface.read_cdf_forecast_values(
        forecast_id, start, end)
    fx_index = forecast_values.index
    utc_start, utc_end = convert_startend(start, end)
    assert (fx_index == TESTINDICES[idx_step].loc[utc_start:utc_end].index).all() # NOQA
    assert (forecast_values.columns == ['value']).all()


def test_read_cdf_forecast_values_invalid_forecast(sql_app, user, startend):
    start, end = startend
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_cdf_forecast_values(
            str(uuid.uuid1()), start, end)


def test_read_cdf_forecast_values_invalid_user(
        sql_app, invalid_user, startend):
    start, end = startend
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_cdf_forecast_values(
            list(demo_single_cdf.keys())[0], start, end)


@pytest.mark.parametrize('forecast_id', demo_single_cdf.keys())
def test_read_latest_cdf_forecast_value(sql_app, user, forecast_id):
    parent_id = demo_single_cdf[forecast_id]['parent']
    idx_step = demo_group_cdf[parent_id]['interval_length']
    forecast_values = storage_interface.read_latest_cdf_forecast_value(
        forecast_id)
    fx_index = forecast_values.index
    assert len(fx_index) == 1
    assert fx_index[0] == TESTINDICES[idx_step].index[-1]
    assert (forecast_values.columns == ['value']).all()


def test_read_latest_cdf_forecast_value_no_data(
        sql_app, user, nocommit_cursor):
    cdf_forecast = {'parent': list(demo_group_cdf.keys())[0],
                    'constant_value': 100.0}
    new_id = storage_interface.store_cdf_forecast(cdf_forecast)
    forecast_values = storage_interface.read_latest_cdf_forecast_value(new_id)
    fx_index = forecast_values.index
    assert len(fx_index) == 0


def test_read_latest_df_forecast_value_invalid_forecast(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_latest_cdf_forecast_value(
            str(uuid.uuid1()))


def test_read_latest_cdf_forecast_value_obs_id(sql_app, user, observation_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_latest_cdf_forecast_value(
            observation_id)


def test_read_latest_cdf_forecast_value_invalid_user(
        sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_cdf_forecast_values(
            list(demo_single_cdf.keys())[0])


@pytest.mark.parametrize('forecast_id', demo_single_cdf.keys())
def test_read_cdf_forecast_time_range(sql_app, user, forecast_id):
    parent_id = demo_single_cdf[forecast_id]['parent']
    idx_step = demo_group_cdf[parent_id]['interval_length']
    trange = storage_interface.read_cdf_forecast_time_range(
        forecast_id)
    assert len(trange) == 2
    assert trange['min_timestamp'] == TESTINDICES[idx_step].index[0]
    assert trange['max_timestamp'] == TESTINDICES[idx_step].index[-1]


def test_read_cdf_forecast_time_range_no_data(sql_app, user, nocommit_cursor):
    cdf_forecast = {'parent': list(demo_group_cdf.keys())[0],
                    'constant_value': 100.0}
    new_id = storage_interface.store_cdf_forecast(cdf_forecast)
    trange = storage_interface.read_cdf_forecast_time_range(new_id)
    assert len(trange) == 2
    assert trange['min_timestamp'] is None
    assert trange['max_timestamp'] is None


def test_read_cdf_forecast_time_range_invalid_forecast(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_cdf_forecast_time_range(
            str(uuid.uuid1()))


def test_read_cdf_forecast_time_range_invalid_user(
        sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_cdf_forecast_time_range(
            list(demo_single_cdf.keys())[0])


@pytest.mark.parametrize('cdf_forecast_id', demo_single_cdf.keys())
def test_store_cdf_forecast_values(sql_app, user, nocommit_cursor,
                                   cdf_forecast_id, fx_vals):
    fx_vals = fx_vals.shift(freq='30d')
    storage_interface.store_cdf_forecast_values(cdf_forecast_id, fx_vals)
    stored = storage_interface.read_cdf_forecast_values(
        cdf_forecast_id, start=fx_vals.index[0])
    pdt.assert_frame_equal(stored, fx_vals, check_freq=False)


def test_store_cdf_forecast_values_nan(sql_app, user, nocommit_cursor,
                                       cdf_forecast_id, fx_vals):
    fx_vals = fx_vals.shift(freq='30d')
    fx_vals.loc[2:4, ['value']] = np.nan
    assert np.isnan(fx_vals['value']).sum() > 0
    storage_interface.store_cdf_forecast_values(cdf_forecast_id, fx_vals)
    stored = storage_interface.read_cdf_forecast_values(
        cdf_forecast_id, start=fx_vals.index[0])
    pdt.assert_frame_equal(stored, fx_vals, check_freq=False)


def test_store_cdf_forecast_values_no_forecast(sql_app, user, nocommit_cursor,
                                               fx_vals):
    new_id = str(uuid.uuid1())
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_cdf_forecast_values(new_id, fx_vals)


def test_store_cdf_forecast_values_invalid_user(sql_app, invalid_user,
                                                nocommit_cursor, fx_vals):
    fx_id = list(demo_single_cdf.keys())[0]
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_cdf_forecast_values(fx_id, fx_vals)


@pytest.mark.parametrize('forecast_id', demo_single_cdf.keys())
def test_read_cdf_forecast_single(sql_app, user, forecast_id):
    single = demo_single_cdf[forecast_id]
    forecast = storage_interface.read_cdf_forecast(forecast_id)
    parent = demo_group_cdf[single['parent']].copy()
    del parent['constant_values']
    parent['constant_value'] = single['constant_value']
    parent['parent'] = single['parent']
    parent['forecast_id'] = forecast_id
    assert forecast == parent


def test_read_cdf_forecast_single_invalid_forecast(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_cdf_forecast(str(uuid.uuid1()))


def test_read_cdf_forecast_single_invalid_user(sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_cdf_forecast(list(demo_single_cdf.keys())[0])


def test_store_cdf_forecast_single(sql_app, user, nocommit_cursor):
    cdf_forecast = {'parent': list(demo_group_cdf.keys())[0],
                    'constant_value': 100.0}
    new_id = storage_interface.store_cdf_forecast(cdf_forecast)
    new_cdf_forecast = storage_interface.read_cdf_forecast(new_id)
    parent = list(demo_group_cdf.values())[0].copy()
    del parent['constant_values']
    parent['constant_value'] = cdf_forecast['constant_value']
    parent['parent'] = cdf_forecast['parent']
    parent['forecast_id'] = new_id
    for key in ('provider', 'modified_at', 'created_at'):
        del parent[key]
        del new_cdf_forecast[key]
    assert new_cdf_forecast == parent


def test_store_cdf_forecast_single_invalid_user(sql_app, invalid_user,
                                                nocommit_cursor):
    cdf_forecast = {'parent': list(demo_group_cdf.keys())[0],
                    'constant_value': 100.0}
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_cdf_forecast(cdf_forecast)


def test_store_cdf_forecast_single_same_parent_value(sql_app, invalid_user,
                                                     nocommit_cursor):
    cdf_forecast = {'parent': list(demo_group_cdf.keys())[0],
                    'constant_value': 5.0}
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_cdf_forecast(cdf_forecast)


@pytest.mark.parametrize('forecast_id', demo_group_cdf.keys())
def test_read_cdf_forecast_group(sql_app, user, forecast_id):
    group = demo_group_cdf[forecast_id].copy()
    forecast = storage_interface.read_cdf_forecast_group(forecast_id)
    group['constant_values'] = {thing['forecast_id']: thing
                                for thing in group['constant_values']}
    forecast['constant_values'] = {thing['forecast_id']: thing
                                   for thing in forecast['constant_values']}
    assert forecast == group


def test_read_cdf_forecast_group_invalid_forecast(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_cdf_forecast_group(str(uuid.uuid1()))


def test_read_cdf_forecast_group_invalid_user(sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_cdf_forecast_group(
            list(demo_group_cdf.keys())[0])


@pytest.mark.parametrize('cdf_forecast', demo_group_cdf.values())
def test_store_cdf_forecast_group(sql_app, user, nocommit_cursor,
                                  cdf_forecast):
    cdf_forecast = cdf_forecast.copy()
    cdf_forecast['constant_values'] = [
        i['constant_value'] for i in cdf_forecast['constant_values']]
    new_id = storage_interface.store_cdf_forecast_group(cdf_forecast)
    new_cdf_forecast = storage_interface.read_cdf_forecast_group(new_id)
    old_cv = set(cdf_forecast['constant_values'])
    new_cv = {i['constant_value'] for i in new_cdf_forecast['constant_values']}
    assert new_cv == old_cv
    for key in ('provider', 'modified_at', 'created_at', 'constant_values',
                'forecast_id'):
        del cdf_forecast[key]
        del new_cdf_forecast[key]
    assert new_cdf_forecast == cdf_forecast


def test_store_cdf_forecast_group_invalid_user(sql_app, invalid_user,
                                               nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_cdf_forecast_group(
            list(demo_group_cdf.values())[0])


def test_list_cdf_forecasts(sql_app, user):
    forecasts = storage_interface.list_cdf_forecasts()
    for fx in forecasts:
        single = demo_single_cdf[fx['forecast_id']]
        parent = demo_group_cdf[single['parent']].copy()
        del parent['constant_values']
        parent['constant_value'] = single['constant_value']
        parent['parent'] = single['parent']
        parent['forecast_id'] = fx['forecast_id']
        assert fx == parent


def test_list_cdf_forecasts_one_parent(sql_app, user):
    parent = list(demo_group_cdf.values())[0].copy()
    forecasts = storage_interface.list_cdf_forecasts(parent['forecast_id'])
    cv = [p['forecast_id'] for p in parent['constant_values']]
    for fx in forecasts:
        assert fx['forecast_id'] in cv
        assert fx['parent'] == parent['forecast_id']


def test_list_cdf_forecasts_invalid_user(sql_app, invalid_user):
    forecasts = storage_interface.list_cdf_forecasts()
    assert len(forecasts) == 0


def test_list_cdf_forecasts_invalid_parent(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.list_cdf_forecasts(str(uuid.uuid1()))


@pytest.mark.parametrize('forecast_id', demo_single_cdf.keys())
def test_delete_cdf_forecast_single(
        sql_app, user, nocommit_cursor, forecast_id):
    storage_interface.delete_cdf_forecast(forecast_id)
    forecast_list = [k['forecast_id']
                     for k in storage_interface.list_cdf_forecasts()]
    assert forecast_id not in forecast_list


def test_delete_cdf_forecast_single_invalid_user(
        sql_app, invalid_user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_cdf_forecast(list(demo_single_cdf.keys())[0])


def test_delete_cdf_forecast_single_does_not_exist(
        sql_app, user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_cdf_forecast(str(uuid.uuid1()))


def test_list_cdf_forecast_groups(sql_app, user):
    forecasts = storage_interface.list_cdf_forecast_groups()
    for fx in forecasts:
        group = demo_group_cdf[fx['forecast_id']].copy()
        group['constant_values'] = {thing['forecast_id']: thing
                                    for thing in group['constant_values']}
        fx['constant_values'] = {thing['forecast_id']: thing
                                 for thing in fx['constant_values']}
        assert fx == group


def test_list_cdf_forecast_groups_site(sql_app, user):
    site = list(demo_sites.keys())[0]
    forecasts = storage_interface.list_cdf_forecast_groups(site_id=site)
    for fx in forecasts:
        group = demo_group_cdf[fx['forecast_id']].copy()
        group['constant_values'] = {thing['forecast_id']: thing
                                    for thing in group['constant_values']}
        fx['constant_values'] = {thing['forecast_id']: thing
                                 for thing in fx['constant_values']}
        assert fx == group
        assert fx['site_id'] == site


def test_list_cdf_forecast_groups_invalid_user(sql_app, invalid_user):
    forecasts = storage_interface.list_cdf_forecast_groups()
    assert len(forecasts) == 0


def test_list_cdf_forecast_groups_invalid_site(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.list_cdf_forecast_groups(str(uuid.uuid1()))


def test_list_cdf_forecast_groups_filter_by_aggregate(
        sql_app, user, aggregate_id):
    forecasts = storage_interface.list_cdf_forecast_groups(
        aggregate_id=aggregate_id)
    assert len(forecasts) > 0
    for fx in forecasts:
        assert fx['aggregate_id'] == aggregate_id


@pytest.mark.parametrize('newparams', [
    {'name': 'updated name'},
    {},
    {'extra_parameters': 'new extra'},
    {'name': 'updated', 'extra_parameters': None},
])
def test_update_cdf_forecast(sql_app, user, nocommit_cursor,
                             newparams, cdf_forecast_group_id):
    cdf_forecast = storage_interface.read_cdf_forecast_group(
        cdf_forecast_group_id)
    storage_interface.update_cdf_forecast_group(
        cdf_forecast_group_id, **newparams)
    updated = storage_interface.read_cdf_forecast_group(
        cdf_forecast_group_id)
    cdf_forecast['forecast_id'] = cdf_forecast_group_id
    cdf_forecast.update({k: v for k, v in newparams.items() if v is not None})
    assert updated.pop('modified_at') >= cdf_forecast.pop('modified_at')
    assert updated == cdf_forecast


def test_update_cdf_forecast_invalid_user(
        sql_app, invalid_user, nocommit_cursor, cdf_forecast_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_cdf_forecast_group(
            cdf_forecast_id, name='new')


def test_update_cdf_forecast_does_not_exist(
        sql_app, invalid_user, nocommit_cursor, missing_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_cdf_forecast_group(missing_id, name='new')


def test_update_cdf_forecast_is_single(sql_app, invalid_user, nocommit_cursor,
                                       cdf_forecast_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_cdf_forecast_group(
            cdf_forecast_id, name='new')


@pytest.mark.parametrize('forecast_id', demo_group_cdf.keys())
def test_delete_cdf_forecast_group(
        sql_app, user, nocommit_cursor, forecast_id):
    storage_interface.delete_cdf_forecast_group(forecast_id)
    forecast_list = [k['forecast_id']
                     for k in storage_interface.list_cdf_forecast_groups()]
    assert forecast_id not in forecast_list


def test_delete_cdf_forecast_group_invalid_user(
        sql_app, invalid_user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_cdf_forecast_group(
            list(demo_group_cdf.keys())[0])


def test_delete_cdf_forecast_group_does_not_exist(
        sql_app, user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_cdf_forecast_group(str(uuid.uuid1()))


def test_store_missing_values(
        sql_app, user, nocommit_cursor, obs_vals):
    observation = list(demo_observations.values())[0]
    observation['name'] = 'new_observation'
    new_id = storage_interface.store_observation(observation)
    missing_indices = obs_vals.index[range(0, obs_vals.index.size, 3)]
    obs_vals.loc[missing_indices, 'value'] = np.nan
    storage_interface.store_observation_values(new_id, obs_vals)
    stored = storage_interface.read_observation_values(new_id)
    pdt.assert_frame_equal(stored, obs_vals, check_freq=False)


@pytest.mark.parametrize('forecast_id', demo_forecasts.keys())
def test_read_wrong_type(sql_app, user, forecast_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation(forecast_id)


@pytest.fixture()
def fake_user(sql_app):
    ctx = sql_app.test_request_context()
    ctx.user = 'auth0|create_me'
    ctx.push()
    yield
    ctx.pop()


@pytest.mark.parametrize('run', range(5))
def test_create_new_user(sql_app, fake_user, run, nocommit_cursor):
    new_id = storage_interface.create_new_user()
    new_user_roles = storage_interface.list_roles()
    new_user = storage_interface.get_current_user_info()
    assert new_id['user_id'] == new_user['user_id']
    assert len(new_user_roles) == 1
    user_role = new_user_roles[0]
    assert user_role['name'] == f'DEFAULT User role {new_user["user_id"]}'
    assert len(user_role['permissions']) == 2
    assert new_user['auth0_id'] == 'auth0|create_me'
    assert new_user['organization'] == 'Unaffiliated'


@pytest.mark.parametrize('observation', demo_observations.values())
def test_read_metadata_for_observation_values(sql_app, user, nocommit_cursor,
                                              observation):
    start = pd.Timestamp('1970-01-02')
    iv, pt, ep = storage_interface.read_metadata_for_observation_values(
        observation['observation_id'], start)
    assert iv == observation['interval_length']
    assert pt is None
    assert isinstance(ep, str)


def test_read_metadata_for_observation_values_start(
        sql_app, user, nocommit_cursor):
    observation = list(demo_observations.values())[0]
    start = pd.Timestamp('2019-09-02')
    iv, pt, ep = storage_interface.read_metadata_for_observation_values(
        observation['observation_id'], start)
    assert iv == observation['interval_length']
    assert isinstance(pt, pd.Timestamp)
    assert pt.tzinfo is not None
    assert isinstance(ep, str)


@pytest.mark.parametrize('forecast', demo_forecasts.values())
def test_read_metadata_for_forecast_values(sql_app, user, nocommit_cursor,
                                           forecast):
    start = pd.Timestamp('1970-01-02')
    iv, pt, ep = storage_interface.read_metadata_for_forecast_values(
        forecast['forecast_id'], start)
    assert iv == forecast['interval_length']
    assert pt is None
    assert isinstance(ep, str)


def test_read_metadata_for_forecast_values_w_obs(
        sql_app, user, nocommit_cursor):
    obs = list(demo_observations.values())[0]
    start = pd.Timestamp('1970-01-02')
    storage_interface.read_metadata_for_observation_values(
            obs['observation_id'], start)
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_metadata_for_forecast_values(
            obs['observation_id'], start)


def test_read_metadata_for_forecast_values_start(
        sql_app, user, nocommit_cursor):
    forecast = list(demo_forecasts.values())[0]
    start = pd.Timestamp('2019-09-02')
    iv, pt, ep = storage_interface.read_metadata_for_forecast_values(
        forecast['forecast_id'], start)
    assert iv == forecast['interval_length']
    assert isinstance(pt, pd.Timestamp)
    assert pt.tzinfo is not None
    assert isinstance(ep, str)


@pytest.mark.parametrize('cdf_forecast_id', demo_single_cdf.keys())
def test_read_metadata_for_cdf_forecast_values(
        sql_app, user, nocommit_cursor, cdf_forecast_id):
    start = pd.Timestamp('1970-01-02')
    iv, pt, ep = storage_interface.read_metadata_for_cdf_forecast_values(
        cdf_forecast_id, start)
    assert iv == demo_group_cdf[demo_single_cdf[
        cdf_forecast_id]['parent']]['interval_length']
    assert pt is None
    assert isinstance(ep, str)


def test_read_metadata_for_cdf_forecast_values_start(
        sql_app, user, nocommit_cursor):
    cdf_forecast_id = list(demo_single_cdf.keys())[0]
    start = pd.Timestamp('2019-09-02')
    iv, pt, ep = storage_interface.read_metadata_for_cdf_forecast_values(
        cdf_forecast_id, start)
    assert iv == demo_group_cdf[demo_single_cdf[
        cdf_forecast_id]['parent']]['interval_length']
    assert isinstance(pt, pd.Timestamp)
    assert pt.tzinfo is not None
    assert isinstance(ep, str)


@pytest.mark.parametrize('aggregate_id', demo_aggregates.keys())
def test_read_aggregate(sql_app, user, aggregate_id):
    aggregate = storage_interface.read_aggregate(aggregate_id)
    assert aggregate == demo_aggregates[aggregate_id]


def test_read_aggregate_invalid_aggregate(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_aggregate(str(uuid.uuid1()))


def test_read_aggregate_not_uuid(sql_app, user):
    with pytest.raises(storage_interface.StorageAuthError) as err:
        storage_interface.read_aggregate('f8dd49fa-23e2-48a0-862b-ba0af6de')
    assert "Incorrect string value" in str(err.value)


def test_read_aggregate_invalid_user(sql_app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_aggregate(list(demo_aggregates.keys())[0])


@pytest.mark.parametrize('aggregate', demo_aggregates.values())
def test_store_aggregate(sql_app, user, aggregate, nocommit_cursor):
    aggregate = aggregate.copy()
    aggregate['name'] = 'new_aggregate'
    new_id = storage_interface.store_aggregate(aggregate)
    new_aggregate = storage_interface.read_aggregate(new_id)
    aggregate['aggregate_id'] = new_id
    for key in ('provider', 'modified_at', 'created_at', 'observations'):
        del aggregate[key]
        del new_aggregate[key]
    assert aggregate == new_aggregate


def test_store_aggregate_invalid_user(
        sql_app, invalid_user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_aggregate(
            list(demo_aggregates.values())[0])


def test_list_aggregates(sql_app, user):
    aggregates = storage_interface.list_aggregates()
    for agg in remove_reference(aggregates):
        assert agg == demo_aggregates[agg['aggregate_id']]


def test_list_aggregates_invalid_user(sql_app, invalid_user):
    aggregates = storage_interface.list_aggregates()
    assert len(aggregates) == 0


@pytest.mark.parametrize('newparams', [
    {'name': 'updated name'},
    {},
    {'extra_parameters': 'new extra', 'timezone': None},
    {'name': 'updated', 'extra_parameters': None,
     'description': 'new desc'},
    {'description': 'is nwe', 'name': None,
     'timezone': 'American/Los Angeles'}
])
def test_update_aggregate(sql_app, user, nocommit_cursor,
                          newparams, aggregate_id):
    aggregate = storage_interface.read_aggregate(aggregate_id)
    storage_interface.update_aggregate(aggregate_id, **newparams)
    updated = storage_interface.read_aggregate(aggregate_id)
    aggregate['aggregate_id'] = aggregate_id
    aggregate.update({k: v for k, v in newparams.items() if v is not None})
    assert updated.pop('modified_at') >= aggregate.pop('modified_at')
    assert updated == aggregate


def test_update_aggregate_invalid_user(sql_app, invalid_user, nocommit_cursor,
                                       aggregate_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_aggregate(aggregate_id, name='new')


def test_update_aggregate_does_not_exist(
        sql_app, invalid_user, nocommit_cursor, missing_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_aggregate(missing_id, name='new')


def test_update_aggregate_access_is_fx(sql_app, invalid_user, nocommit_cursor,
                                       forecast_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.update_aggregate(forecast_id, name='new')


@pytest.mark.parametrize('aggregate_id', demo_aggregates.keys())
def test_delete_aggregate(sql_app, user, nocommit_cursor, aggregate_id):
    storage_interface.delete_aggregate(aggregate_id)
    aggregate_list = [
        k['aggregate_id'] for k in storage_interface.list_aggregates()]
    assert aggregate_id not in aggregate_list


def test_delete_aggregate_invalid_user(
        sql_app, invalid_user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_aggregate(list(demo_aggregates.keys())[0])


def test_delete_aggregate_does_not_exist(sql_app, user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_aggregate(str(uuid.uuid1()))


@pytest.mark.parametrize('aggregate_id', demo_aggregates.keys())
def test_add_observation_to_aggregate(
        sql_app, user, nocommit_cursor, aggregate_id):
    obs_id = '9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f'
    aggregate = storage_interface.read_aggregate(aggregate_id)
    obs_before = {
        obs['observation_id'] for obs in aggregate['observations']}
    assert obs_id not in obs_before
    storage_interface.add_observation_to_aggregate(aggregate_id, obs_id)
    aggregate = storage_interface.read_aggregate(aggregate_id)
    obs_before.add(obs_id)
    assert obs_before == {
        obs['observation_id'] for obs in aggregate['observations']}


def test_add_observation_to_aggregate_time(sql_app, user, nocommit_cursor):
    aggregate_id = list(demo_aggregates.keys())[0]
    obs_id = '9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f'
    ef = dt.datetime(2019, 9, 12, 13, 49, tzinfo=dt.timezone.utc)
    storage_interface.add_observation_to_aggregate(aggregate_id, obs_id, ef)
    aggregate = storage_interface.read_aggregate(aggregate_id)
    for obs in aggregate['observations']:
        if obs['observation_id'] == obs_id:
            assert obs['effective_from'] == ef


def test_add_observation_to_aggregate_denied(
        sql_app, invalid_user, nocommit_cursor):
    aggregate_id = list(demo_aggregates.keys())[0]
    obs_id = '9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f'
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.add_observation_to_aggregate(
            aggregate_id, obs_id)


def test_add_observation_to_aggregate_cant_read_obs(
        sql_app, user, nocommit_cursor):
    aggregate_id = list(demo_aggregates.keys())[0]
    obs_id = '825fa192-824f-11e9-a81f-54bf64606445'
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.add_observation_to_aggregate(
            aggregate_id, obs_id)


def test_add_observation_to_aggregate_obs_present(
        sql_app, user, nocommit_cursor):
    aggregate_id = list(demo_aggregates.keys())[0]
    obs_id = demo_aggregates[aggregate_id][
        'observations'][0]['observation_id']
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.add_observation_to_aggregate(
            aggregate_id, obs_id)


@pytest.mark.parametrize('aggregate_id', demo_aggregates.keys())
def test_remove_observation_from_aggregate(
        sql_app, user, nocommit_cursor, aggregate_id):
    obs_id = demo_aggregates[aggregate_id][
        'observations'][0]['observation_id']
    aggregate = storage_interface.read_aggregate(aggregate_id)
    assert all([obs['effective_until'] is None
                for obs in aggregate['observations']])
    storage_interface.remove_observation_from_aggregate(aggregate_id, obs_id)
    aggregate = storage_interface.read_aggregate(aggregate_id)
    for obs in aggregate['observations']:
        if obs['observation_id'] == obs_id:
            assert obs['effective_until'] is not None
        else:
            assert obs['effective_until'] is None


def test_remove_observation_from_aggregate_time(
        sql_app, user, nocommit_cursor):
    aggregate_id = list(demo_aggregates.keys())[0]
    obs_id = demo_aggregates[aggregate_id][
        'observations'][0]['observation_id']
    et = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
          ).replace(microsecond=0)
    storage_interface.remove_observation_from_aggregate(aggregate_id, obs_id,
                                                        et)
    aggregate = storage_interface.read_aggregate(aggregate_id)
    for obs in aggregate['observations']:
        if obs['observation_id'] == obs_id:
            assert obs['effective_until'] == et
        else:
            assert obs['effective_until'] is None


def test_remove_observation_from_aggregate_denied(
        sql_app, invalid_user, nocommit_cursor):
    aggregate_id = list(demo_aggregates.keys())[0]
    obs_id = demo_aggregates[aggregate_id][
        'observations'][0]['observation_id']
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.remove_observation_from_aggregate(
            aggregate_id, obs_id)


def test_read_aggregate_values(sql_app, user, nocommit_cursor,
                               ghi_obs_vals):
    aggregate_id = list(demo_aggregates.keys())[0]
    out = storage_interface.read_aggregate_values(aggregate_id)
    assert isinstance(out, dict)
    # no data in db for 825fa193-824f-11e9-a81f-54bf64606445
    assert set(out.keys()) == {
        "123e4567-e89b-12d3-a456-426655440000",
        "e0da0dea-9482-4073-84de-f1b12c304d23",
        "b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2"}

    for df in out.values():
        pdt.assert_frame_equal(df, ghi_obs_vals)


def test_read_aggregate_values_denied(sql_app, invalid_user, nocommit_cursor):
    aggregate_id = list(demo_aggregates.keys())[0]
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_aggregate_values(aggregate_id)


def test_read_aggregate_values_restricted_start_end(
        sql_app, user, nocommit_cursor, ghi_obs_vals):
    aggregate_id = list(demo_aggregates.keys())[0]
    start = pd.Timestamp('20190415T0000Z')
    end = pd.Timestamp('20190416T0000Z')
    out = storage_interface.read_aggregate_values(aggregate_id, start, end)
    assert isinstance(out, dict)
    # no data in db for 825fa193-824f-11e9-a81f-54bf64606445
    assert set(out.keys()) == {
        "123e4567-e89b-12d3-a456-426655440000",
        "e0da0dea-9482-4073-84de-f1b12c304d23",
        "b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2"}

    for df in out.values():
        pdt.assert_frame_equal(
            df, ghi_obs_vals[start:end])


def test_read_aggregate_values_adj_effective_from(sql_app, user,
                                                  nocommit_cursor):
    aggregate_id = list(demo_aggregates.keys())[0]
    change_id = "123e4567-e89b-12d3-a456-426655440000"
    storage_interface.remove_observation_from_aggregate(
        aggregate_id, change_id, pd.Timestamp('20190101T0000Z'))
    storage_interface.add_observation_to_aggregate(
        aggregate_id, change_id, pd.Timestamp('20190416T0000Z'))
    remove_id = "e0da0dea-9482-4073-84de-f1b12c304d23"
    storage_interface.remove_observation_from_aggregate(
        aggregate_id, remove_id, pd.Timestamp('20190417T0000Z'))
    out = storage_interface.read_aggregate_values(aggregate_id)
    assert isinstance(out, dict)
    # no data in db for 825fa193-824f-11e9-a81f-54bf64606445
    assert set(out.keys()) == {
        "123e4567-e89b-12d3-a456-426655440000",
        "e0da0dea-9482-4073-84de-f1b12c304d23",
        "b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2"}
    assert out[change_id].index[0] == pd.Timestamp('20190416T0000Z')
    assert out[remove_id].index[-1] == pd.Timestamp('20190417T0000Z')


def test_read_aggregate_values_effective_overlap(sql_app, user,
                                                 nocommit_cursor):
    aggregate_id = list(demo_aggregates.keys())[0]
    change_id = "123e4567-e89b-12d3-a456-426655440000"
    storage_interface.remove_observation_from_aggregate(
        aggregate_id, change_id, pd.Timestamp('20190101T0000Z'))
    # effective from 4/16 to 4/17
    storage_interface.add_observation_to_aggregate(
        aggregate_id, change_id, pd.Timestamp('20190416T0000Z'))
    storage_interface.remove_observation_from_aggregate(
        aggregate_id, change_id, pd.Timestamp('20190417T0000Z'))
    # effective from 4/15 onward
    storage_interface.add_observation_to_aggregate(
        aggregate_id, change_id, pd.Timestamp('20190415T0000Z'))
    out = storage_interface.read_aggregate_values(aggregate_id)
    assert isinstance(out, dict)
    # no data in db for 825fa193-824f-11e9-a81f-54bf64606445
    assert set(out.keys()) == {
        "123e4567-e89b-12d3-a456-426655440000",
        "e0da0dea-9482-4073-84de-f1b12c304d23",
        "b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2"}
    assert out[change_id].index[0] == pd.Timestamp('20190415T0000Z')
    assert out[change_id].index[-1] > pd.Timestamp('20190417T0000Z')
    assert (out[change_id].index == out[change_id].index.unique()).all()


def test_read_aggregate_values_empty(sql_app, user, nocommit_cursor):
    aggregate_id = list(demo_aggregates.keys())[0]
    start = pd.Timestamp('20190915T0000Z')
    end = pd.Timestamp('20190916T0000Z')
    out = storage_interface.read_aggregate_values(aggregate_id, start, end)
    assert isinstance(out, dict)
    assert not out


def test_read_user_id(sql_app, user, nocommit_cursor, external_userid,
                      external_auth0id):
    out = storage_interface.read_user_id(external_auth0id)
    assert out == external_userid


def test_read_user_id_self(sql_app, user, nocommit_cursor, user_id,
                           auth0id):
    out = storage_interface.read_user_id(auth0id)
    assert out == user_id


def test_read_user_id_fail(sql_app, user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_user_id('auth0|random')


def test_create_job_user(mocker, orgid):
    app = create_app('AdminTestConfig')
    create = mocker.patch('sfa_api.utils.auth0_info.create_user',
                          return_value='auth0|testuser')
    mocker.patch('sfa_api.utils.auth0_info.get_refresh_token',
                 return_value='token')
    with app.app_context():
        try:
            storage_interface.mysql_connection()
        except pymysql.err.OperationalError:
            pytest.skip('No connection to test database')
        with _make_nocommit_cursor(mocker):
            uid, aid = storage_interface.create_job_user(
                'testuser', 'testpw', orgid, Fernet.generate_key())
    assert aid == 'auth0|testuser'
    assert isinstance(uid, str)
    assert create.call_args[0] == ('testuser', 'testpw', True)


def test_create_job_user_bad_sql_user(
        sql_app, nocommit_cursor, mocker, orgid):
    mocker.patch('sfa_api.utils.auth0_info.create_user',
                 return_value='auth0|testuser')
    mocker.patch('sfa_api.utils.auth0_info.get_refresh_token',
                 return_value='token')
    with pytest.raises(pymysql.err.InternalError):
        storage_interface.create_job_user(
            'testuser', 'testpw', orgid, Fernet.generate_key())


def test_list_reports(sql_app, report, user):
    out = storage_interface.list_reports()
    assert len(out) == 1
    exp = report.copy()
    exp.pop('raw_report', None)
    exp.pop('values', None)
    assert out[0] == exp


def test_list_reports_bad_user(sql_app, report, invalid_user):
    out = storage_interface.list_reports()
    assert len(out) == 0


def test_store_report(sql_app, user, report_parameters, nocommit_cursor):
    id_ = storage_interface.store_report(
        {'report_parameters': report_parameters})
    out = storage_interface.read_report(id_)
    assert out['report_parameters'] == report_parameters
    assert out['report_id'] == id_
    assert out['status'] == 'pending'


def test_store_report_denied(sql_app, invalid_user, report_parameters):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_report(
            {'report_parameters': report_parameters})


def test_read_report(sql_app, report, user, reportid):
    out = storage_interface.read_report(reportid)
    assert out == report


def test_read_report_values_missing(sql_app, report, user, reportid,
                                    remove_perms_from_current_role):
    remove_perms_from_current_role('read_values', 'reports')
    out = storage_interface.read_report(reportid)
    assert out['report_parameters'] == report['report_parameters']
    assert out['values'] != report['values']
    assert out['values'] == []


def test_read_report_denied(sql_app, invalid_user, reportid):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_report(reportid)


def test_delete_report(sql_app, user, nocommit_cursor, reportid):
    storage_interface.delete_report(reportid)
    assert len(storage_interface.list_reports()) == 0


def test_delete_report_denied(sql_app, invalid_user,
                              nocommit_cursor, reportid):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.delete_report(reportid)


def test_store_report_values(sql_app, user, reportid, report_values,
                             nocommit_cursor):
    newid = storage_interface.store_report_values(
        reportid, report_values['object_id'],
        report_values['processed_values'])
    vals = storage_interface.read_report_values(reportid)
    assert len(vals) == 2
    assert newid in [v['id'] for v in vals]


def test_store_report_values_denied(sql_app, invalid_user, reportid,
                                    report_values):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_report_values(
            reportid, report_values['object_id'],
            report_values['processed_values'])


def test_read_report_values(sql_app, user, reportid, report):
    out = storage_interface.read_report_values(reportid)
    assert out == report['values']


def test_read_report_values_denied(sql_app, invalid_user, reportid):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_report_values(reportid)


def test_store_raw_report(sql_app, user, nocommit_cursor, reportid,
                          report, raw_report_json):
    rr = raw_report_json.copy()
    rr['messages'] = ['first']
    storage_interface.store_raw_report(reportid, rr)
    rep = storage_interface.read_report(reportid)
    raw = rep['raw_report']
    assert raw.pop('messages') == ['first']
    exp = report['raw_report']
    exp.pop('messages')
    assert raw == exp


def test_store_raw_report_denied(
        sql_app, invalid_user, nocommit_cursor, reportid, raw_report_json):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_raw_report(reportid, raw_report_json)


def test_store_report_status(sql_app, user, nocommit_cursor, reportid):
    storage_interface.store_report_status(reportid, 'failed')
    rep = storage_interface.read_report(reportid)
    assert rep['status'] == 'failed'


def test_store_report_status_denied(
        sql_app, invalid_user, nocommit_cursor, reportid):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_report_status(reportid, 'failed')


@pytest.mark.parametrize('inp,exp', [
    ('NaN', storage_interface.NANSTR),
    ('aNaN', 'aNaN'),
    ('a NaN', 'a NaN'),
    ('"NaN', '"NaN'),
    (', NaN', ', ' + storage_interface.NANSTR),
    ('[NaN,', '[' + storage_interface.NANSTR + ','),
    ('Infinity', storage_interface.INFSTR),
    (', Infinity', ', ' + storage_interface.INFSTR),
    ('[Infinity,', '[' + storage_interface.INFSTR + ','),
    ('-Infinity', storage_interface.NINFSTR),
    (',-Infinity', ',' + storage_interface.NINFSTR),
    ('[-Infinity,', '[' + storage_interface.NINFSTR + ','),
])
def test_replace(inp, exp):
    assert storage_interface._replace(inp) == exp


@pytest.mark.parametrize('inp,exp', [
    ('allyourbase', '"allyourbase"'),
    (math.nan, storage_interface.NANSTR),
    ('NaN', '"NaN"'),
    (math.inf, storage_interface.INFSTR),
    (-1 * math.inf, storage_interface.NINFSTR),
    ([math.nan, math.inf],
     f'[{storage_interface.NANSTR}, {storage_interface.INFSTR}]'),
    ({'Infinity': math.inf, 'NaN': math.nan},
     f'{{"Infinity": {storage_interface.INFSTR}, '
     f'"NaN": {storage_interface.NANSTR}}}'),
    ('dict: 12', '"dict: 12"'),
    # known failure when ther is what looks like a dict in a string
    pytest.param('notdict: NaN, other', '"notdict: NaN, other"',
                 marks=pytest.mark.xfail(strict=True))
])
def test_dump_json_replace_nan(inp, exp):
    out = storage_interface.dump_json_replace_nan(inp)
    json.loads(out)  # should be valid json
    assert out == exp


def naneq(inp, exp):
    def eq(a, b):
        return a == b or (math.isnan(a) and math.isnan(b))

    if type(inp) != type(exp):
        return False
    if isinstance(inp, list):
        if len(inp) != len(exp):
            return False
        for i, v in enumerate(inp):
            if not naneq(exp[i], v):
                return False
        return True
    elif isinstance(inp, dict):
        if set(inp.keys()) != set(exp.keys()):
            return False
        for k, v in inp.items():
            if not naneq(exp[k], v):
                return False
        return True
    else:
        return eq(inp, exp)


@pytest.mark.parametrize('a,b,res', [
    ('asdf', 'asdf', True),
    ({'a': math.nan, 'b': math.inf}, {'b': math.inf, 'a': math.nan}, True),
    ([math.nan, 1, 2, 3], [None, 1, 2, 3], False),
    ([1, 2, 3], [1, 2], False),
    ({'a': math.nan}, {'b': math.nan, 'a': math.inf}, False),
    ({'a': math.inf}, {'a': -1 * math.inf}, False),
])
def test_naneq(a, b, res):
    assert naneq(a, b) is res


@pytest.mark.parametrize('inp', [
    'allyourbase',
    math.nan,
    'NaN',
    math.inf,
    -1 * math.inf,
    'Infinity',
    [math.nan, math.inf],
    ['Nan', math.nan],
    ['\'Nan\'', math.nan],
    ['"NaN"', 'Infinity'],
    [-1 * math.inf, math.inf, math.nan],
    'allInfinityother',
    'beforNaNandmore',
    {'val': math.nan, 'Other': 'NaN'},
])
def test_json_replace_nan_roundtrip(inp):
    inter = storage_interface.dump_json_replace_nan(inp)
    # make sure valid json w/o nan or inf
    assert 'INVALID' not in json.loads(
        inter, parse_constant=lambda x: 'INVALID')
    out = storage_interface.load_json_replace_nan(inter)
    assert naneq(out, inp)


def test_store_raw_report_nan_metric(
        sql_app, user, nocommit_cursor, reportid,
        report, raw_report_json):
    rr = raw_report_json.copy()
    rr['messages'] = ['first']
    rr['metrics'] = [{'name': 'name', 'forecast_id': '', 'observation_id': '',
                      'aggregate_id': '', 'values': [{
                          'category': 'date', 'metric': 'r', 'index': '0',
                          'value': math.nan}]}]
    storage_interface.store_raw_report(reportid, rr)
    rep = storage_interface.read_report(reportid)
    raw = rep['raw_report']
    assert raw.pop('messages') == ['first']
    exp = report['raw_report']
    exp.pop('messages')
    omet = raw.pop('metrics')
    raw['metrics'] = []
    assert raw == exp
    assert naneq(omet, rr['metrics'])


def test_call_procedure_bad_json(
        sql_app, user, nocommit_cursor, reportid):
    with pytest.raises(storage_interface.BadAPIRequest):
        storage_interface._call_procedure('store_raw_report', reportid,
                                          '{"badnan": NaN}')


def test_get_user_actions_on_object(
        sql_app, user, nocommit_cursor, forecast_id):
    actions = storage_interface.get_user_actions_on_object(forecast_id)
    assert sorted(actions) == sorted(['read', 'read_values', 'delete',
                                      'delete_values', 'write_values',
                                      'update'])


def test_get_user_actions_on_object_object_dne(
        sql_app, user, nocommit_cursor, missing_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.get_user_actions_on_object(missing_id)


def test_get_user_actions_on_object_no_actions(
        sql_app, user, nocommit_cursor, inaccessible_forecast_id):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.get_user_actions_on_object(inaccessible_forecast_id)


def test_list_zones(sql_app):
    zones = storage_interface.list_zones()
    assert {z['name'] for z in zones} == {f'Reference Region {i}'
                                          for i in range(1, 10)}
    for zone in zones:
        assert 'created_at' in zone
        assert 'modified_at' in zone


def test_read_zone(sql_app):
    geojson = storage_interface.read_climate_zone('Reference Region 9')
    assert geojson['type'] == 'FeatureCollection'


def test_read_zone_dne(sql_app):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_climate_zone('Reference Region 11')


@pytest.mark.parametrize('lat,lon,zones', [
    (32.2, -110.0, {'Reference Region 3'}),
    (43, -73.0, {'Reference Region 7'}),
    (20, -110, set())
])
def test_find_zone(sql_app, lat, lon, zones):
    res = storage_interface.find_climate_zones(lat, lon)
    szones = {r['name'] for r in res}
    assert zones == szones


@pytest.mark.parametrize('observation_id', demo_observations.keys())
def test_find_unflagged_observation_dates(sql_app, user, observation_id,
                                          obs_vals, nocommit_cursor):
    start = pd.Timestamp('20190415T1205Z')
    end = pd.Timestamp('20190418T1215Z')
    # more varied qf
    obs_vals['quality_flag'] = 2
    obs_vals.loc[start:start+pd.Timedelta('1d'), 'quality_flag'] |= 12
    storage_interface.store_observation_values(observation_id, obs_vals)
    dates = storage_interface.find_unflagged_observation_dates(
        observation_id, start, end, 8)
    assert dates == [dt.date(2019, 4, 16),
                     dt.date(2019, 4, 17)]
    dates = storage_interface.find_unflagged_observation_dates(
        observation_id, start, end, 1, 'Etc/GMT+12')
    assert dates == [dt.date(2019, 4, 15),
                     dt.date(2019, 4, 16)]
    # all validated
    dates = storage_interface.find_unflagged_observation_dates(
        observation_id, start, end, 2)
    assert dates == []

    # compound flag
    dates = storage_interface.find_unflagged_observation_dates(
        observation_id, start, end, 9)
    assert dates == [dt.date(2019, 4, 15),
                     dt.date(2019, 4, 16),
                     dt.date(2019, 4, 17)]


def test_read_unflagged_observation_dates_invalid_observation(sql_app, user):
    start = pd.Timestamp('20190414T1205Z')
    end = pd.Timestamp('20190417T1215Z')
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.find_unflagged_observation_dates(
            str(uuid.uuid1()), start, end, 0)


def test_read_unflagged_observation_dates_invalid_is_fx(sql_app, user,
                                                        forecast_id):
    start = pd.Timestamp('20190414T1205Z')
    end = pd.Timestamp('20190417T1215Z')
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.find_unflagged_observation_dates(
            forecast_id, start, end, 0)


@pytest.mark.parametrize('observation_id', demo_observations.keys())
def test_find_observation_gaps(sql_app, user, observation_id, nocommit_cursor):
    start = pd.Timestamp('20190413T1205Z')
    end = pd.Timestamp('20190418T1215Z')
    obs_vals = pd.DataFrame({'value': 0, 'quality_flag': 2},
                            index=[start, start + pd.Timedelta('10min')])
    storage_interface.store_observation_values(observation_id, obs_vals)
    ds = storage_interface.find_observation_gaps(observation_id, start, end)
    assert ds[0]['timestamp'] == start.to_pydatetime()
    assert ds[0]['next_timestamp'] == (
        start + pd.Timedelta('10min')).to_pydatetime()
    assert ds[1]['timestamp'] == (
        start + pd.Timedelta('10min')).to_pydatetime()
    assert ds[1]['next_timestamp'] == (
        pd.Timestamp('20190414T07:00Z')).to_pydatetime()


def test_find_observation_gaps_invalid_observation(sql_app, user):
    start = pd.Timestamp('20190414T1205Z')
    end = pd.Timestamp('20190417T1215Z')
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.find_observation_gaps(
            str(uuid.uuid1()), start, end)


def test_find_observation_gaps_invalid_is_fx(sql_app, user,
                                             forecast_id):
    start = pd.Timestamp('20190414T1205Z')
    end = pd.Timestamp('20190417T1215Z')
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.find_observation_gaps(
            forecast_id, start, end)


@pytest.mark.parametrize('forecast_id', demo_forecasts.keys())
def test_find_forecast_gaps(sql_app, user, forecast_id, nocommit_cursor):
    start = pd.Timestamp('20180413T1205Z')
    end = pd.Timestamp('20180418T1215Z')
    il = pd.Timedelta(f"{demo_forecasts[forecast_id]['interval_length']}min")
    vals = pd.DataFrame({'value': 0},
                        index=[start, start + 3 * il,
                               start + 4 * il,
                               start + 7 * il])
    storage_interface.store_forecast_values(forecast_id, vals)
    ds = storage_interface.find_forecast_gaps(forecast_id, start, end)
    assert ds[0]['timestamp'] == start.to_pydatetime()
    assert ds[0]['next_timestamp'] == vals.index[1].to_pydatetime()
    assert ds[1]['timestamp'] == vals.index[2].to_pydatetime()
    assert ds[1]['next_timestamp'] == vals.index[3].to_pydatetime()


def test_find_forecast_gaps_invalid_forecast(sql_app, user):
    start = pd.Timestamp('20190414T1205Z')
    end = pd.Timestamp('20190417T1215Z')
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.find_forecast_gaps(
            str(uuid.uuid1()), start, end)


def test_find_forecast_gaps_invalid_is_obs(sql_app, user,
                                           observation_id):
    start = pd.Timestamp('20190414T1205Z')
    end = pd.Timestamp('20190417T1215Z')
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.find_forecast_gaps(
            observation_id, start, end)


@pytest.mark.parametrize('cdf_forecast_id', demo_single_cdf.keys())
def test_find_cdf_forecast_gaps(sql_app, user, cdf_forecast_id,
                                nocommit_cursor):
    start = pd.Timestamp('20180413T1205Z')
    end = pd.Timestamp('20180418T1215Z')
    il = pd.Timedelta(
        f"{demo_group_cdf[demo_single_cdf[cdf_forecast_id]['parent']]['interval_length']}min")  # NOQA
    vals = pd.DataFrame({'value': 0},
                        index=[start, start + 3 * il,
                               start + 4 * il,
                               start + 7 * il])
    storage_interface.store_cdf_forecast_values(cdf_forecast_id, vals)
    ds = storage_interface.find_cdf_forecast_gaps(cdf_forecast_id, start, end)
    assert ds[0]['timestamp'] == start.to_pydatetime()
    assert ds[0]['next_timestamp'] == vals.index[1].to_pydatetime()
    assert ds[1]['timestamp'] == vals.index[2].to_pydatetime()
    assert ds[1]['next_timestamp'] == vals.index[3].to_pydatetime()


def test_find_cdf_forecast_gaps_invalid_cdf_forecast(sql_app, user):
    start = pd.Timestamp('20190414T1205Z')
    end = pd.Timestamp('20190417T1215Z')
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.find_cdf_forecast_gaps(
            str(uuid.uuid1()), start, end)


def test_find_cdf_forecast_gaps_invalid_is_obs(sql_app, user,
                                               observation_id):
    start = pd.Timestamp('20190414T1205Z')
    end = pd.Timestamp('20190417T1215Z')
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.find_cdf_forecast_gaps(
            observation_id, start, end)


@pytest.mark.parametrize('cdf_group_id', demo_group_cdf.keys())
def test_find_cdf_forecast_group_gaps(sql_app, user, cdf_group_id,
                                      nocommit_cursor):
    start = pd.Timestamp('20180413T1205Z')
    end = pd.Timestamp('20180418T1215Z')
    il = pd.Timedelta(
        f"{demo_group_cdf[cdf_group_id]['interval_length']}min")  # NOQA
    vals = pd.DataFrame({'value': 0},
                        index=[start, start + 3 * il,
                               start + 4 * il,
                               start + 7 * il])
    cdf_forecast_id = [k for k, v in demo_single_cdf.items()
                       if v['parent'] == cdf_group_id][0]
    storage_interface.store_cdf_forecast_values(cdf_forecast_id, vals)
    ds = storage_interface.find_cdf_forecast_group_gaps(
        cdf_group_id, start, end)
    assert ds[0]['timestamp'] == start.to_pydatetime()
    assert ds[0]['next_timestamp'] == vals.index[1].to_pydatetime()
    assert ds[1]['timestamp'] == vals.index[2].to_pydatetime()
    assert ds[1]['next_timestamp'] == vals.index[3].to_pydatetime()


def test_find_cdf_forecast_group_gaps_invalid_cdf_forecast(sql_app, user):
    start = pd.Timestamp('20190414T1205Z')
    end = pd.Timestamp('20190417T1215Z')
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.find_cdf_forecast_group_gaps(
            str(uuid.uuid1()), start, end)


def test_find_cdf_forecast_group_gaps_invalid_is_obs(sql_app, user,
                                                     observation_id):
    start = pd.Timestamp('20190414T1205Z')
    end = pd.Timestamp('20190417T1215Z')
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.find_cdf_forecast_group_gaps(
            observation_id, start, end)


def test__site_has_modeling_params(sql_app, user, site_id_plant):
    assert storage_interface._site_has_modeling_params(site_id_plant)


def test_site_has_modeling_params_weather_site(sql_app, user, site_id):
    assert not storage_interface._site_has_modeling_params(site_id)


@pytest.mark.parametrize('variable', [
    'ghi', 'dni', 'dhi', 'air_temperature', 'wind_speed',
    'relative_humidity', 'event', 'net_load',
])
def test__check_for_power_variables_weather_var(
        sql_app, user, site_id, variable):
    storage_interface._check_for_power_variables(variable, site_id)


@pytest.mark.parametrize('variable', [
    'ac_power', 'dc_power', 'availability', 'poa_global', 'curtailment',
])
def test__check_for_power_variables_failure(
        sql_app, user, site_id, variable):
    with pytest.raises(storage_interface.BadAPIRequest):
        storage_interface._check_for_power_variables(variable, site_id)


@pytest.mark.parametrize('variable', [
    'ac_power', 'dc_power', 'availability', 'poa_global', 'curtailment',
])
def test__check_for_power_variables_power_var_at_plant(
        sql_app, user, site_id_plant, variable):
    storage_interface._check_for_power_variables(variable, site_id_plant)


def test__assert_variable_matches_aggregate(sql_app, user, aggregate_id):
    storage_interface._assert_variable_matches_aggregate('ghi', aggregate_id)


def test__assert_variable_matches_aggregate_failure(
        sql_app, user, aggregate_id):
    with pytest.raises(storage_interface.BadAPIRequest):
        storage_interface._assert_variable_matches_aggregate(
            'dni', aggregate_id)
    storage_interface._assert_variable_matches_aggregate('ghi', aggregate_id)


def test_get_user_creatable_types(sql_app, user, nocommit_cursor):
    objects = storage_interface.get_user_creatable_types()
    assert objects == ['sites', 'aggregates', 'cdf_forecasts', 'forecasts',
                       'observations', 'roles', 'permissions', 'reports']


@pytest.mark.parametrize('object_type,expected_actions', [
    ('observations', ['read', 'delete', 'read_values',
                      'write_values', 'delete_values']),
    ('forecasts', ['read', 'delete', 'read_values', 'write_values',
                   'delete_values']),
    ('cdf_forecasts', ['read', 'update', 'delete', 'read_values',
                       'write_values', 'delete_values']),
    ('roles', ['read', 'update', 'delete', 'grant', 'revoke']),
    ('permissions', ['read', 'update', 'delete']),
    ('users', ['read', 'update']),
    ('reports', ['read', 'update', 'delete', 'read_values',
                 'write_values']),
])
def test_list_actions_on_all_objects_of_type(
        sql_app, user, object_type, expected_actions):
    object_list = storage_interface.list_actions_on_all_objects_of_type(
        object_type)
    # Test user is granted "applies_to_all" permissions, so we can assert that
    # each object has the same permissions
    for o in object_list:
        assert o['actions'].sort() == expected_actions.sort()
