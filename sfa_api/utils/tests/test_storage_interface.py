import datetime as dt
import math
import uuid


import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest
import pymysql


from sfa_api.demo.sites import static_sites as demo_sites
from sfa_api.demo.observations import static_observations as demo_observations
from sfa_api.demo.forecasts import static_forecasts as demo_forecasts
from sfa_api.demo.cdf_forecasts import static_cdf_forecasts as demo_single_cdf
from sfa_api.demo.cdf_forecasts import static_cdf_forecast_groups as demo_group_cdf  # NOQA
from sfa_api.demo import values
from sfa_api.utils import storage_interface


TESTINDICES = {
    1: values.generate_randoms(1)[0].to_series(keep_tz=True),
    5: values.generate_randoms(5)[0].to_series(keep_tz=True),
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


def test_store_observation_invalid_user(
        sql_app, invalid_user, nocommit_cursor):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_observation(
            list(demo_observations.values())[0])


@pytest.mark.parametrize('observation', demo_observations.values())
def test_store_observation_values(sql_app, user, nocommit_cursor,
                                  observation):
    observation['name'] = 'new_observation'
    new_id = storage_interface.store_observation(observation)
    obs_vals = values.static_observation_values()
    storage_interface.store_observation_values(new_id, obs_vals)
    stored = storage_interface.read_observation_values(new_id)
    pdt.assert_frame_equal(stored, obs_vals)


def test_store_observation_values_tz(sql_app, user, nocommit_cursor):
    observation = list(demo_observations.values())[0]
    observation['name'] = 'new_observation'
    new_id = storage_interface.store_observation(observation)
    obs_vals = values.static_observation_values()
    storage_interface.store_observation_values(
        new_id, obs_vals.tz_convert('MST'))
    stored = storage_interface.read_observation_values(new_id)
    pdt.assert_frame_equal(stored, obs_vals)


def test_store_observation_values_no_observation(
        sql_app, user, nocommit_cursor):
    new_id = str(uuid.uuid1())
    obs_vals = values.static_observation_values()
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_observation_values(new_id, obs_vals)


def test_store_observation_values_invalid_user(sql_app, invalid_user,
                                               nocommit_cursor):
    obs_id = list(demo_observations.keys())[0]
    obs_vals = values.static_observation_values()
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_observation_values(obs_id, obs_vals)


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
                               forecast):
    forecast['name'] = 'new_forecast'
    new_id = storage_interface.store_forecast(forecast)
    fx_vals = values.static_forecast_values()
    storage_interface.store_forecast_values(new_id, fx_vals)
    stored = storage_interface.read_forecast_values(new_id)
    pdt.assert_frame_equal(stored, fx_vals)


def test_store_forecast_values_tz(sql_app, user, nocommit_cursor):
    forecast = list(demo_forecasts.values())[0]
    forecast['name'] = 'new_forecast'
    new_id = storage_interface.store_forecast(forecast)
    fx_vals = values.static_forecast_values()
    storage_interface.store_forecast_values(new_id, fx_vals.tz_convert('MST'))
    stored = storage_interface.read_forecast_values(new_id)
    pdt.assert_frame_equal(stored, fx_vals)


def test_store_forecast_values_no_forecast(sql_app, user, nocommit_cursor):
    new_id = str(uuid.uuid1())
    fx_vals = values.static_forecast_values()
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_forecast_values(new_id, fx_vals)


def test_store_forecast_values_invalid_user(sql_app, invalid_user,
                                            nocommit_cursor):
    fx_id = list(demo_forecasts.keys())[0]
    fx_vals = values.static_forecast_values()
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_forecast_values(fx_id, fx_vals)


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


@pytest.mark.parametrize('cdf_forecast_id', demo_single_cdf.keys())
def test_store_cdf_forecast_values(sql_app, user, nocommit_cursor,
                                   cdf_forecast_id):
    fx_vals = values.static_forecast_values().shift(freq='30d')
    storage_interface.store_cdf_forecast_values(cdf_forecast_id, fx_vals)
    stored = storage_interface.read_cdf_forecast_values(
        cdf_forecast_id, start=fx_vals.index[0])
    pdt.assert_frame_equal(stored, fx_vals)


def test_store_cdf_forecast_values_no_forecast(sql_app, user, nocommit_cursor):
    new_id = str(uuid.uuid1())
    fx_vals = values.static_forecast_values()
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.store_cdf_forecast_values(new_id, fx_vals)


def test_store_cdf_forecast_values_invalid_user(sql_app, invalid_user,
                                                nocommit_cursor):
    fx_id = list(demo_single_cdf.keys())[0]
    fx_vals = values.static_forecast_values()
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
    forecasts = storage_interface.list_cdf_forecast_groups(site)
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
        sql_app, user, nocommit_cursor):
    observation = list(demo_observations.values())[0]
    observation['name'] = 'new_observation'
    new_id = storage_interface.store_observation(observation)
    obs_vals = values.static_observation_values()
    missing_indices = range(0, obs_vals.index.size, 3)
    obs_vals['value'].iloc[missing_indices] = pd.np.nan
    storage_interface.store_observation_values(new_id, obs_vals)
    stored = storage_interface.read_observation_values(new_id)
    pdt.assert_frame_equal(stored, obs_vals)


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
def test_create_new_user(sql_app, fake_user, run):
    storage_interface.create_new_user()
    new_user_roles = storage_interface.list_roles()
    new_user = storage_interface.get_current_user_info()
    assert len(new_user_roles) == 1
    user_role = new_user_roles[0]
    assert user_role['name'] == f'DEFAULT User role {new_user["user_id"]}'
    assert len(user_role['permissions']) == 2
    assert new_user['auth0_id'] == 'auth0|create_me'
    assert new_user['organization'] == 'Unaffiliated'
