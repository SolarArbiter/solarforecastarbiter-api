from collections import OrderedDict
import datetime as dt
import json
import os
from uuid import uuid1, UUID


import pytest
import pymysql


@pytest.fixture(scope='session')
def connection():
    connection = pymysql.connect(
        host=os.getenv('MYSQL_HOST', '127.0.0.1'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user='root',
        password='testpassword',
        database='arbiter_data',
        binary_prefix=True)
    # with no connection.commit(), no data should stay in db
    return connection


@pytest.fixture()
def cursor(connection):
    connection.rollback()
    return connection.cursor()


@pytest.fixture()
def dictcursor(connection):
    connection.rollback()
    return connection.cursor(cursor=pymysql.cursors.DictCursor)


def uuid_to_bin(uuid):
    """Copy mysql UUID_TO_BIN with time swap of hi and low"""
    if uuid is None:
        return None
    return uuid.bytes[6:8] + uuid.bytes[4:6] + uuid.bytes[:4] + uuid.bytes[8:]


def bin_to_uuid(binid):
    """Copy mysql BIN_TO_UUID"""
    if binid is None:
        return None
    return str(UUID(bytes=binid[4:8] + binid[2:4] + binid[:2] + binid[8:]))


def newuuid():
    return uuid_to_bin(uuid1())


@pytest.fixture(scope='function')
def new_organization(cursor):
    def fnc():
        out = OrderedDict(id=newuuid(), name=f'org{str(uuid1())[:10]}')
        cursor.execute(
            'INSERT INTO organizations (id, name, accepted_tou)'
            'VALUES (%s, %s, TRUE)',
            list(out.values()))
        return out
    return fnc


@pytest.fixture()
def new_report(
        cursor, new_organization, new_observation,
        new_forecast, new_cdf_forecast):
    def fcn(org=None, observation=None, forecasts=None, cdf_forecasts=None):
        if org is None:
            org = new_organization()
        if observation is None:
            obs = new_observation()
        else:
            obs = observation
        if not forecasts:
            fx1 = new_forecast()
            fx2 = new_forecast()
            fx_list = [fx1, fx2]
        else:
            fx_list = forecasts.copy()
        if cdf_forecasts is None:
            cdf_forecast = new_cdf_forecast()
            cdf_fx = [cdf_forecast]
        else:
            cdf_fx = cdf_forecasts.copy()
        fx_list.extend(cdf_fx)
        name = f'report{str(uuid1())[:10]}'
        report_parameters = {
            'name': name,
            'object_pairs': [(str(bin_to_uuid(obs['id'])),
                              str(bin_to_uuid(fx['id'])))
                             for fx in fx_list],
            'start': (dt.datetime.now() - dt.timedelta(weeks=1)).isoformat(),
            'end': dt.datetime.now().isoformat(),
            'metrics': ['MAE', 'RMSE'],
        }
        params_json = json.dumps(report_parameters)
        out = OrderedDict(id=newuuid(), organization_id=org['id'],
                          name=name,
                          report_parameters=params_json)
        insert_dict(cursor, 'reports', out)
        for obj in fx_list + [obs]:
            cursor.execute(
                'INSERT INTO report_values (id, report_id, object_id, '
                'processed_values) VALUES (%s, %s, %s, BINARY(RAND()))',
                (newuuid(), out['id'], obj['id']))
        return out
    return fcn


@pytest.fixture()
def new_user(cursor, new_organization):
    def fcn(org=None):
        if org is None:
            org = new_organization()
        out = OrderedDict(id=newuuid(), auth0_id=f'authid{str(uuid1())[:10]}',
                          organization_id=org['id'])
        cursor.execute(
            'INSERT INTO users (id, auth0_id, organization_id) VALUES '
            '(%s, %s, %s)', list(out.values()))
        return out
    return fcn


@pytest.fixture()
def new_role(cursor, new_organization):
    def fcn(org=None):
        if org is None:
            org = new_organization()
        out = OrderedDict(id=newuuid(), name=f'role{str(uuid1())[:10]}',
                          description='therole',
                          organization_id=org['id'])
        cursor.execute(
            'INSERT INTO roles (id, name, description, organization_id) '
            'VALUES (%s, %s, %s, %s)', list(out.values()))
        return out
    return fcn


@pytest.fixture()
def new_permission(cursor, new_organization):
    def fcn(action, object_type, applies_to_all, org=None):
        if org is None:
            org = new_organization()
        out = OrderedDict(id=newuuid(), description='perm',
                          organization_id=org['id'],
                          action=action, object_type=object_type,
                          applies_to_all=applies_to_all)
        cursor.execute(
            'INSERT INTO permissions (id, description, organization_id, action'
            ', object_type, applies_to_all) VALUES (%s, %s, %s, %s, %s, %s)',
            list(out.values()))
        return out
    return fcn


def insert_dict(cursor, table, thedict):
    cursor.execute(
        f'INSERT INTO {table} ({",".join(thedict.keys())}) VALUES'
        f' ({",".join(["%s" for _ in range(len(thedict.keys()))])})',
        list(thedict.values()))


@pytest.fixture()
def new_site(cursor, new_organization):
    def fcn(org=None, latitude=0, longitude=0):
        if org is None:
            org = new_organization()
        out = OrderedDict(id=newuuid(), organization_id=org['id'],
                          name=f'site{str(uuid1())[:10]}',
                          latitude=latitude, longitude=longitude, elevation=0,
                          timezone='America/Denver', extra_parameters='',
                          ac_capacity=0, dc_capacity=0,
                          temperature_coefficient=0,
                          tracking_type='fixed',
                          surface_tilt=0, surface_azimuth=0,
                          axis_tilt=None, axis_azimuth=None,
                          ground_coverage_ratio=None,
                          backtrack=None,
                          max_rotation_angle=None,
                          dc_loss_factor=0,
                          ac_loss_factor=0)
        insert_dict(cursor, 'sites', out)
        return out
    return fcn


@pytest.fixture()
def new_forecast(cursor, new_site):
    def fcn(site=None, org=None, aggregate=None):
        if aggregate is not None and site is None:
            siteid = None
            orgid = aggregate['organization_id']
            aggid = aggregate['id']
        elif site is None:
            site = new_site(org)
            siteid = site['id']
            orgid = site['organization_id']
            aggid = None
        else:
            siteid = site['id']
            aggid = None
            orgid = site['organization_id']

        out = OrderedDict(
            id=newuuid(), organization_id=orgid,
            site_id=siteid, aggregate_id=aggid,
            name=f'forecast{str(uuid1())[:10]}',
            variable='power', issue_time_of_day='12:00',
            lead_time_to_start=60, interval_label='beginning',
            interval_length=60, run_length=1440,
            interval_value_type='interval_mean', extra_parameters='')
        insert_dict(cursor, 'forecasts', out)
        # add some  test data too
        cursor.execute(
            'INSERT INTO forecasts_values (id, timestamp, value) VALUES '
            '(%s, TIMESTAMP(\'2020-01-01 11:03\'), RAND())', (out['id'], ))
        return out
    return fcn


@pytest.fixture()
def new_cdf_forecast(cursor, new_site):
    def fcn(site=None, org=None, aggregate=None):
        if aggregate is not None and site is None:
            siteid = None
            orgid = aggregate['organization_id']
            aggid = aggregate['id']
        elif site is None:
            site = new_site(org)
            siteid = site['id']
            orgid = site['organization_id']
            aggid = None
        else:
            siteid = site['id']
            aggid = None
            orgid = site['organization_id']

        out = OrderedDict(
            id=newuuid(), organization_id=orgid,
            site_id=siteid, aggregate_id=aggid,
            name=f'forecast{str(uuid1())[:10]}',
            variable='power', issue_time_of_day='12:00',
            lead_time_to_start=60, interval_label='beginning',
            interval_length=60, run_length=1440,
            interval_value_type='interval_mean', extra_parameters='',
            axis='x')
        insert_dict(cursor, 'cdf_forecasts_groups', out)
        out['constant_values'] = {}
        for i in range(3):
            id = uuid1()
            single = OrderedDict(
                id=uuid_to_bin(id), cdf_forecast_group_id=out['id'],
                constant_value=i)
            insert_dict(cursor, 'cdf_forecasts_singles', single)
            # add some  test data too
            cursor.execute(
                'INSERT INTO cdf_forecasts_values (id, timestamp, value) '
                'VALUES (%s, TIMESTAMP(\'2020-01-03 18:01\'), RAND())',
                (single['id'], ))
            out['constant_values'][str(id)] = float(i)
        return out
    return fcn


@pytest.fixture()
def new_observation(cursor, new_site):
    def fcn(site=None, org=None):
        if site is None:
            site = new_site(org)
        out = OrderedDict(
            id=newuuid(), organization_id=site['organization_id'],
            site_id=site['id'], name=f'observation{str(uuid1())[:10]}',
            variable='power', interval_label='instant',
            interval_length=5, interval_value_type='instantaneous',
            uncertainty=0.05, extra_parameters='')
        insert_dict(cursor, 'observations', out)
        cursor.execute(
            'INSERT INTO observations_values (id, timestamp, value, '
            'quality_flag) VALUES (%s, TIMESTAMP(\'2020-01-03 10:00\'), RAND(), 0)',
            (out['id'], ))
        return out
    return fcn


@pytest.fixture()
def new_aggregate(cursor, new_observation):
    def fcn(obs_list=None, site=None, org=None):
        if obs_list is None:
            obs_list = [new_observation(site, org)]
        if org is None:
            org_id = obs_list[0]['organization_id']
        else:
            org_id = org['id']
        out = OrderedDict(
            id=newuuid(), organization_id=org_id,
            name=f'aggregate{str(uuid1())[:10]}',
            description='An aggregate',
            variable='power',
            timezone='America/Denver',
            interval_label='ending',
            interval_length=15,
            aggregate_type='sum',
            extra_parameters='')
        insert_dict(cursor, 'aggregates', out)
        cursor.executemany(
            'INSERT INTO aggregate_observation_mapping '
            '(aggregate_id, observation_id, effective_from) VALUES (%s, %s,'
            'TIMESTAMP("2019-01-01 00:00"))',
            [(out['id'], obs['id']) for obs in obs_list]
        )
        out['interval_value_type'] = 'interval_mean'
        out['obs_list'] = obs_list
        return out
    return fcn


@pytest.fixture(params=['sites', 'users', 'roles', 'forecasts',
                        'observations', 'cdf_forecasts', 'reports',
                        'aggregates'])
def getfcn(request, new_site, new_user, new_role, new_forecast,
           new_observation, new_cdf_forecast, new_report,
           new_aggregate):
    if request.param == 'sites':
        return new_site, 'sites'
    elif request.param == 'users':
        return new_user, 'users'
    elif request.param == 'roles':
        return new_role, 'roles'
    elif request.param == 'forecasts':
        return new_forecast, 'forecasts'
    elif request.param == 'observations':
        return new_observation, 'observations'
    elif request.param == 'cdf_forecasts':
        return new_cdf_forecast, 'cdf_forecasts'
    elif request.param == 'reports':
        return new_report, 'reports'
    elif request.param == 'aggregates':
        return new_aggregate, 'aggregates'


@pytest.fixture()
def valueset(cursor, new_organization, new_user, new_role, new_permission,
             new_site, new_forecast, new_observation, new_cdf_forecast,
             new_report, new_aggregate):
    org0 = new_organization()
    org1 = new_organization()
    user0 = new_user(org=org0)
    user1 = new_user(org=org1)
    role0 = new_role(org=org0)
    role1 = new_role(org=org1)
    role2 = new_role(org=org0)
    cursor.executemany(
        "INSERT INTO user_role_mapping (user_id, role_id) VALUES (%s, %s)",
        [(user0['id'], role0['id']), (user1['id'], role1['id']),
         (user1['id'], role2['id'])])
    site0 = new_site(org=org0)
    site1 = new_site(org=org1)
    perm0 = new_permission('read', 'forecasts', False, org=org0)
    perm1 = new_permission('read', 'forecasts', False, org=org0)
    perm2 = new_permission('read', 'forecasts', True, org=org1)
    perm3 = new_permission('read', 'reports', False, org=org0)
    crossperm = new_permission('read', 'forecasts', False, org=org0)
    createperm = new_permission('create', 'forecasts', True, org=org0)
    forecasts0 = [new_forecast(site=site0) for _ in range(4)]
    forecasts1 = [new_forecast(site=site1) for _ in range(2)]
    forecasts2 = new_forecast(site=site0)
    obs0 = new_observation(site=site0)
    obs1 = new_observation(site=site0)
    obs2 = new_observation(site=site1)
    agg0 = new_aggregate(obs_list=[obs0, obs1])
    agg1 = new_aggregate(obs_list=[obs0, obs1, obs2], org=org1)
    forecasts3 = new_forecast(aggregate=agg0)
    cdf0 = new_cdf_forecast(site=site0)
    cdf1 = new_cdf_forecast(site=site1)
    cdf2 = new_cdf_forecast(aggregate=agg0)
    rep0 = new_report(org0, obs0, forecasts0, [cdf0])
    rep1 = new_report(org1, obs2, forecasts1, [cdf1])
    cursor.executemany(
        "INSERT INTO role_permission_mapping (role_id, permission_id) "
        "VALUES (%s, %s)",
        [(role0['id'], perm0['id']), (role0['id'], perm1['id']),
         (role1['id'], perm2['id']), (role2['id'], crossperm['id']),
         (role0['id'], createperm['id']), (role1['id'], createperm['id']),
         (role0['id'], perm3['id'])])
    cursor.executemany(
        "INSERT INTO permission_object_mapping (permission_id, object_id) "
        "VALUES (%s, %s)", [(perm0['id'], forecasts0[0]['id']),
                            (perm0['id'], forecasts0[1]['id']),
                            (perm1['id'], forecasts0[2]['id']),
                            (perm1['id'], forecasts0[3]['id']),
                            (crossperm['id'], forecasts2['id']),
                            (perm3['id'], rep0['id'])])
    return ((org0, org1), (user0, user1), (role0, role1, role2),
            (site0, site1),
            (perm0, perm1, perm2, crossperm, createperm),
            forecasts0 + forecasts1 + [forecasts2, forecasts3],
            (obs0, obs1, obs2), (cdf0, cdf1, cdf2), (rep0, rep1),
            (agg0, agg1))


@pytest.fixture(params=[0, 1])
def valueset_org(valueset, request):
    return valueset[0][request.param]


@pytest.fixture(params=[0, 1])
def valueset_user(valueset, request):
    return valueset[1][request.param]


@pytest.fixture(params=[0, 1, 2])
def valueset_role(valueset, request):
    return valueset[2][request.param]


@pytest.fixture(params=[0, 1])
def valueset_site(valueset, request):
    return valueset[3][request.param]


@pytest.fixture(params=list(range(4)))  # ignore create perm
def valueset_permission(valueset, request):
    return valueset[4][request.param]


@pytest.fixture(params=list(range(7)))
def valueset_forecast(valueset, request):
    return valueset[5][request.param]


@pytest.fixture(params=list(range(3)))
def valueset_observation(valueset, request):
    return valueset[6][request.param]


@pytest.fixture(params=[0, 1])
def valueset_report(valueset, request):
    return valueset[8][request.param]


@pytest.fixture(params=[0, 1])
def valueset_aggregate(valueset, request):
    return valueset[9][request.param]


@pytest.fixture()
def allow_grant_roles(cursor, new_permission, valueset):
    org = valueset[0][0]
    role = valueset[2][0]
    perm = new_permission('grant', 'roles', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id)'
        ' VALUES (%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_revoke_roles(cursor, new_permission, valueset):
    org = valueset[0][0]
    role = valueset[2][0]
    perm = new_permission('revoke', 'roles', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id)'
        ' VALUES (%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def new_organization_no_tou(cursor):
    def fnc():
        out = OrderedDict(id=newuuid(), name=f'org{str(uuid1())[:10]}')
        cursor.execute(
            'INSERT INTO organizations (id, name, accepted_tou)'
            'VALUES (%s, %s, FALSE)',
            list(out.values()))
        return out
    return fnc


@pytest.fixture()
def unaffiliated_organization(dictcursor):
    dictcursor.execute(
        'SELECT * FROM organizations WHERE name = "Unaffiliated"')
    org = dictcursor.fetchone()
    return org


@pytest.fixture()
def new_unaffiliated_user(cursor, unaffiliated_organization):
    def fnc():
        out = OrderedDict(id=newuuid(), auth0_id=f'authid{str(uuid1())[:10]}',
                          organization_id=unaffiliated_organization['id'])
        cursor.execute(
            'INSERT INTO users (id, auth0_id, organization_id) VALUES '
            '(%s, %s, %s)', list(out.values()))
        return out
    return fnc


@pytest.fixture()
def default_user_role(cursor, valueset):
    org = valueset[0][0]
    user = valueset[1][0]
    cursor.execute('CALL create_default_user_role(%s, %s)',
                   (user['id'], org['id']))
    return user


@pytest.fixture()
def new_job(cursor, new_user):
    def fnc(user=None, name='testjob'):
        if user is None:
            user = new_user()
        out = OrderedDict(
            id=newuuid(),
            organization_id=user['organization_id'],
            user_id=user['id'],
            name=name,
            job_type='daily_observation_validation',
            parameters='{"start_td": "1h"}',
            schedule='{"type": "cron", "cron_schedule": "* * * * *"}',
            version=0
        )
        cursor.execute(
            'INSERT INTO scheduled_jobs (id, organization_id, user_id, name, '
            'job_type, parameters, schedule, version) VALUES'
            ' (%s, %s, %s, %s, %s, %s, %s, %s)', list(out.values()))
        return out
    return fnc


@pytest.fixture()
def new_climzone(cursor):
    def fnc(name='USA', coords=(
            (-130, 20), (-65, 20),
            (-65, 50), (-130, 50), (-130, 20)),
            insert=True
            ):
        geojson = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {
                "name": "urn:ogc:def:crs:EPSG::4326"}},
            "features": [
                {"type": "Feature",
                 "properties": {"Name": name},
                 "geometry": {"type": "Polygon", "coordinates": [
                     coords
                 ]}
                 }
            ]
        }
        if insert:
            cursor.execute(
                'INSERT INTO climate_zones (name, g) VALUES '
                '(%s, ST_GeomFromGeoJSON(%s))',
                (name, json.dumps(geojson))
            )
        return geojson
    return fnc
