from collections import namedtuple, OrderedDict
from decimal import Decimal


import pymysql
import pytest


from conftest import bin_to_uuid


@pytest.fixture()
def insertuser(cursor, new_permission, valueset, new_user):
    AllMeta = namedtuple('AllMeta', ['user', 'site', 'fx', 'obs', 'org',
                                     'role', 'cdf', 'auth0id', 'agg', 'agg_fx',
                                     'agg_cdf'])
    org = valueset[0][0]
    user = valueset[1][0]
    role = valueset[2][0]
    site = valueset[3][0]
    fx = valueset[5][0]
    agg_fx = valueset[5][-1]
    obs = valueset[6][0]
    cdf = valueset[7][0]
    agg_cdf = valueset[7][2]
    agg = valueset[9][0]

    for thing in (user, site, fx, obs, cdf, agg_fx, agg_cdf, agg):
        thing['strid'] = str(bin_to_uuid(thing['id']))
    cursor.execute(
        "DELETE FROM permissions WHERE action = 'update'")
    return AllMeta(user, site, fx, obs, org, role, cdf,
                   user['auth0_id'], agg, agg_fx, agg_cdf)


@pytest.fixture()
def allow_update_observations(new_permission, cursor, insertuser):
    perm = new_permission('update', 'observations', True,
                          org=insertuser.org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)', (insertuser.role['id'], perm['id']))


@pytest.fixture()
def allow_update_forecasts(new_permission, cursor, insertuser):
    perm = new_permission('update', 'forecasts', True,
                          org=insertuser.org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)', (insertuser.role['id'], perm['id']))


@pytest.fixture()
def allow_update_cdf_forecasts(new_permission, cursor, insertuser):
    perm = new_permission('update', 'cdf_forecasts', True,
                          org=insertuser.org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)', (insertuser.role['id'], perm['id']))


@pytest.fixture()
def allow_update_sites(new_permission, cursor, insertuser):
    perm = new_permission('update', 'sites', True,
                          org=insertuser.org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)', (insertuser.role['id'], perm['id']))


@pytest.fixture()
def allow_update_aggregates(new_permission, cursor, insertuser):
    perm = new_permission('update', 'aggregates', True,
                          org=insertuser.org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)', (insertuser.role['id'], perm['id']))


@pytest.fixture()
def get_id(insertuser):
    def fcn(thing):
        return getattr(insertuser, thing)['strid']
    return fcn


@pytest.mark.parametrize('name', [
    'New NAME', None, pytest.param(0, marks=pytest.mark.xfail(strict=True))])
@pytest.mark.parametrize('uncertainty', [
    1.9, None, pytest.param('a', marks=pytest.mark.xfail(strict=True))])
@pytest.mark.parametrize('extra_parameters', [
    '', 'New extra', None,
    pytest.param(0, marks=pytest.mark.xfail(strict=True))])
def test_update_observation(dictcursor, insertuser, allow_update_observations,
                            name, uncertainty, extra_parameters):
    dictcursor.execute('SELECT * from arbiter_data.observations WHERE id = %s',
                       insertuser.obs['id'])
    expected = dictcursor.fetchall()[0]
    assert expected['name'] != name
    assert expected['uncertainty'] != uncertainty
    dictcursor.callproc(
        'update_observation', (
            insertuser.auth0id, insertuser.obs['strid'],
            name, uncertainty, extra_parameters
        ))
    dictcursor.execute('SELECT * from arbiter_data.observations WHERE id = %s',
                       insertuser.obs['id'])
    new = dictcursor.fetchall()[0]
    if name is not None:
        expected['name'] = name
    if uncertainty is not None:
        expected['uncertainty'] = uncertainty
    if extra_parameters is not None:
        expected['extra_parameters'] = extra_parameters
    assert new.pop('modified_at') >= expected.pop('modified_at')
    assert new == expected


@pytest.mark.parametrize('idtype', ['obs', 'fx'])
def test_update_observation_denied(dictcursor, insertuser, get_id, idtype,
                                   allow_update_forecasts):
    id_ = get_id(idtype)
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'update_observation', (
                insertuser.auth0id, id_,
                'new name', 0, 'new exxtra'
            ))
    assert e.value.args[0] == 1142


@pytest.mark.parametrize('name', [
    'New NAME', None, pytest.param(0, marks=pytest.mark.xfail(strict=True))])
@pytest.mark.parametrize('extra_parameters', [
    'New extra', None, pytest.param(0, marks=pytest.mark.xfail(strict=True))])
@pytest.mark.parametrize('fxtype', ['fx', 'agg_fx'])
def test_update_forecast(dictcursor, insertuser, allow_update_forecasts,
                         name, extra_parameters, fxtype):
    fx = getattr(insertuser, fxtype)
    dictcursor.execute('SELECT * from arbiter_data.forecasts WHERE id = %s',
                       fx['id'])
    expected = dictcursor.fetchall()[0]
    assert expected['name'] != name
    assert expected['extra_parameters'] != extra_parameters
    dictcursor.callproc(
        'update_forecast', (
            insertuser.auth0id, fx['strid'],
            name, extra_parameters
        ))
    dictcursor.execute('SELECT * from arbiter_data.forecasts WHERE id = %s',
                       fx['id'])
    new = dictcursor.fetchall()[0]
    if name is not None:
        expected['name'] = name
    if extra_parameters is not None:
        expected['extra_parameters'] = extra_parameters
    assert new.pop('modified_at') >= expected.pop('modified_at')
    assert new == expected


@pytest.mark.parametrize('idtype', ['fx', 'agg_fx', 'cdf'])
def test_update_forecast_denied(dictcursor, insertuser, get_id, idtype,
                                allow_update_cdf_forecasts):
    id_ = get_id(idtype)
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'update_forecast', (
                insertuser.auth0id, id_,
                'new name', 'new exxtra'
            ))
    assert e.value.args[0] == 1142


@pytest.mark.parametrize('name', [
    'New NAME', None, pytest.param(0, marks=pytest.mark.xfail(strict=True))])
@pytest.mark.parametrize('extra_parameters', [
    'New extra', None, pytest.param(0, marks=pytest.mark.xfail(strict=True))])
@pytest.mark.parametrize('fxtype', ['cdf', 'agg_cdf'])
def test_update_cdf_forecast(
        dictcursor, insertuser, allow_update_cdf_forecasts,
        name, extra_parameters, fxtype):
    cdf = getattr(insertuser, fxtype)
    dictcursor.execute(
        'SELECT * from arbiter_data.cdf_forecasts_groups WHERE id = %s',
        cdf['id'])
    expected = dictcursor.fetchall()[0]
    assert expected['name'] != name
    assert expected['extra_parameters'] != extra_parameters
    dictcursor.callproc(
        'update_cdf_forecast', (
            insertuser.auth0id, cdf['strid'],
            name, extra_parameters
        ))
    dictcursor.execute(
        'SELECT * from arbiter_data.cdf_forecasts_groups WHERE id = %s',
        cdf['id'])
    new = dictcursor.fetchall()[0]
    if name is not None:
        expected['name'] = name
    if extra_parameters is not None:
        expected['extra_parameters'] = extra_parameters
    assert new.pop('modified_at') >= expected.pop('modified_at')
    assert new == expected


@pytest.mark.parametrize('idtype', ['cdf', 'fx', 'agg_cdf'])
def test_update_cdf_forecast_denied(dictcursor, get_id, idtype, insertuser,
                                    allow_update_forecasts):
    id_ = get_id(idtype)
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'update_cdf_forecast', (
                insertuser.auth0id, id_,
                'new name', 'new exxtra'
            ))
    assert e.value.args[0] == 1142


@pytest.mark.parametrize('kwargs', [
    OrderedDict(
        name='new nm',
        latitude=None, longitude=-93, elevation=999, timezone='America/Denver',
        extra_parameters=None, ac_capacity=None, dc_capacity=0,
        temperature_coefficient=0, tracking_type='single_axis',
        surface_tilt=None, surface_azimuth=10, axis_tilt=None,
        axis_azimuth=None, ground_coverage_ratio=None,
        backtrack=True, max_rotation_angle=0, dc_loss_factor=None,
        ac_loss_factor=None),
    OrderedDict(
        name=None,
        latitude=33, longitude=-110, elevation=None, timezone=None,
        extra_parameters='extra', ac_capacity=1.9, dc_capacity=None,
        temperature_coefficient=None, tracking_type=None,
        surface_tilt=30, surface_azimuth=None, axis_tilt=0,
        axis_azimuth=180, ground_coverage_ratio=0.2,
        backtrack=None, max_rotation_angle=None, dc_loss_factor=99,
        ac_loss_factor=0),
    pytest.param(
        OrderedDict(
            name=0,
            latitude=33, longitude=-110, elevation=None, timezone=None,
            extra_parameters='extra', ac_capacity=1.9, dc_capacity=0,
            temperature_coefficient=None, tracking_type=None,
            surface_tilt=30, surface_azimuth=None, axis_tilt=0,
            axis_azimuth=180, ground_coverage_ratio=0.2,
            backtrack=None, max_rotation_angle=None, dc_loss_factor=99,
            ac_loss_factor=0), marks=pytest.mark.xfail(strict=True)),
    pytest.param(
        OrderedDict(
            name='isok',
            latitude=33, longitude=-110, elevation=None, timezone=None,
            extra_parameters='ex', ac_capacity=1.9, dc_capacity=0,
            temperature_coefficient=None, tracking_type=None,
            surface_tilt=30, surface_azimuth=None, axis_tilt=0,
            axis_azimuth=180, ground_coverage_ratio=0.2,
            backtrack=None, max_rotation_angle=None, dc_loss_factor=99,
            ac_loss_factor=999999.92138923),
        marks=pytest.mark.xfail(strict=True))
])
def test_update_site(dictcursor, insertuser, allow_update_sites,
                     kwargs):
    dictcursor.execute(
        'SELECT * from arbiter_data.sites WHERE id = %s',
        insertuser.site['id'])
    expected = dictcursor.fetchall()[0]
    dictcursor.callproc(
        'update_site', tuple([
            insertuser.auth0id, insertuser.site['strid'],
            ] + list(kwargs.values())))
    dictcursor.execute('SELECT * from arbiter_data.sites WHERE id = %s',
                       insertuser.site['id'])
    new = dictcursor.fetchall()[0]
    for k, v in new.items():
        if k not in kwargs or (
                k in ('latitude', 'longitude', 'name', 'elevation',
                      'timezone', 'extra_parameters') and kwargs[k] is None
                ):
            assert v == expected[k]
        else:
            if isinstance(v, Decimal):
                assert v == Decimal(str(kwargs[k]))
            else:
                assert v == kwargs[k]


@pytest.mark.parametrize('kwargs', [
    OrderedDict(
        name='new nm',
        latitude=None, longitude=-93, elevation=999, timezone='America/Denver',
        extra_parameters=None, ac_capacity=None, dc_capacity=0,
        temperature_coefficient=0, tracking_type='noupdate',
        surface_tilt=None, surface_azimuth=10, axis_tilt=None,
        axis_azimuth=None, ground_coverage_ratio=None,
        backtrack=True, max_rotation_angle=0, dc_loss_factor=None,
        ac_loss_factor=None),
    OrderedDict(
        name=None,
        latitude=33, longitude=-110, elevation=None, timezone=None,
        extra_parameters='extra', ac_capacity=1.9, dc_capacity=None,
        temperature_coefficient=None, tracking_type='noupdate',
        surface_tilt=30, surface_azimuth=None, axis_tilt=0,
        axis_azimuth=180, ground_coverage_ratio=0.2,
        backtrack=None, max_rotation_angle=None, dc_loss_factor=99,
        ac_loss_factor=0),
])
def test_update_site_no_modeling_params(
        dictcursor, insertuser, allow_update_sites, kwargs):
    dictcursor.execute(
        'SELECT * from arbiter_data.sites WHERE id = %s',
        insertuser.site['id'])
    expected = dictcursor.fetchall()[0]
    dictcursor.callproc(
        'update_site', tuple([
            insertuser.auth0id, insertuser.site['strid'],
            ] + list(kwargs.values())))
    dictcursor.execute('SELECT * from arbiter_data.sites WHERE id = %s',
                       insertuser.site['id'])
    new = dictcursor.fetchall()[0]
    for k, v in kwargs.items():
        nv = new[k]
        if k in ('latitude', 'longitude', 'name', 'elevation',
                 'timezone', 'extra_parameters'):
            if v is not None:
                if isinstance(nv, Decimal):
                    assert float(nv) == v
                else:
                    assert nv == v
            else:
                assert nv == expected[k]
        else:
            assert nv == expected[k]


@pytest.mark.parametrize('idtype', ['site', 'fx'])
def test_update_site_denied(dictcursor, insertuser, get_id, idtype,
                            allow_update_forecasts):
    id_ = get_id(idtype)
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'update_site', (
                insertuser.auth0id, id_,
                'new name', None, None, None, None, 'extra', 0, 0,
                None, None, None, None,
                None, None, None, None, None, 0, 1
            ))
    assert e.value.args[0] == 1142


@pytest.mark.parametrize('name', [
    'New NAME', None])
@pytest.mark.parametrize('description', [
    '', 'ne desc', None,
    pytest.param(0, marks=pytest.mark.xfail(strict=True))])
@pytest.mark.parametrize('timezone', ['America/Phoenix', None])
@pytest.mark.parametrize('extra_parameters', [
    'New extra', None])
def test_update_aggregate(dictcursor, insertuser, allow_update_aggregates,
                          name, description, extra_parameters, timezone):
    dictcursor.execute('SELECT * from arbiter_data.aggregates WHERE id = %s',
                       insertuser.agg['id'])
    expected = dictcursor.fetchall()[0]
    assert expected['name'] != name
    dictcursor.callproc(
        'update_aggregate', (
            insertuser.auth0id, insertuser.agg['strid'],
            name, description, timezone, extra_parameters
        ))
    dictcursor.execute('SELECT * from arbiter_data.aggregates WHERE id = %s',
                       insertuser.agg['id'])
    new = dictcursor.fetchall()[0]
    if name is not None:
        expected['name'] = name
    if description is not None:
        expected['description'] = description
    if timezone is not None:
        expected['timezone'] = timezone
    if extra_parameters is not None:
        expected['extra_parameters'] = extra_parameters
    assert new.pop('modified_at') >= expected.pop('modified_at')
    assert new == expected


@pytest.mark.parametrize('idtype', ['agg', 'fx'])
def test_update_aggregate_denied(dictcursor, insertuser, get_id, idtype,
                                 allow_update_forecasts):
    id_ = get_id(idtype)
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'update_aggregate', (
                insertuser.auth0id, id_,
                'new name', 'new desc', 'new tz', 'new exxtra'
            ))
    assert e.value.args[0] == 1142
