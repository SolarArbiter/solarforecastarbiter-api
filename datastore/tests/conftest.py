from collections import OrderedDict
import datetime as dt
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
    return uuid.bytes[6:8] + uuid.bytes[4:6] + uuid.bytes[:4] + uuid.bytes[8:]


def bin_to_uuid(binid):
    """Copy mysql BIN_TO_UUID"""
    return UUID(bytes=binid[4:8] + binid[2:4] + binid[:2] + binid[8:])


def newuuid():
    return uuid_to_bin(uuid1())


@pytest.fixture(scope='function')
def new_organization(cursor):
    def fnc():
        out = OrderedDict(id=newuuid(), name=f'org{str(uuid1())[:10]}')
        cursor.execute('INSERT INTO organizations (id, name) VALUES (%s, %s)',
                       list(out.values()))
        return out
    return fnc


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
    def fcn(org=None):
        if org is None:
            org = new_organization()
        out = OrderedDict(id=newuuid(), organization_id=org['id'],
                          name=f'site{str(uuid1())[:10]}',
                          latitude=0, longitude=0, elevation=0,
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
    def fcn(site=None, org=None):
        if site is None:
            site = new_site(org)
        out = OrderedDict(
            id=newuuid(), organization_id=site['organization_id'],
            site_id=site['id'], name=f'forecast{str(uuid1())[:10]}',
            variable='power', issue_time_of_day='12:00',
            lead_time_to_start=60, interval_label='beginning',
            interval_length=60, run_length=1440,
            interval_value_type='interval_mean', extra_parameters='')
        insert_dict(cursor, 'forecasts', out)
        # add some  test data too
        cursor.execute(
            'INSERT INTO forecasts_values (id, timestamp, value) VALUES '
            '(%s, CURRENT_TIMESTAMP(), RAND())', (out['id'], ))
        return out
    return fcn


@pytest.fixture()
def new_cdf_forecast(cursor, new_site):
    def fcn(site=None, org=None):
        if site is None:
            site = new_site(org)
        out = OrderedDict(
            id=newuuid(), organization_id=site['organization_id'],
            site_id=site['id'], name=f'forecast{str(uuid1())[:10]}',
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
                'VALUES (%s, CURRENT_TIMESTAMP(), RAND())', (single['id'], ))
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
            'quality_flag) VALUES (%s, CURRENT_TIMESTAMP(), RAND(), 0)',
            (out['id'], ))
        return out
    return fcn


@pytest.fixture(params=['sites', 'users', 'roles', 'forecasts',
                        'observations'])
def getfcn(request, new_site, new_user, new_role, new_forecast,
           new_observation):
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


@pytest.fixture()
def valueset(cursor, new_organization, new_user, new_role, new_permission,
             new_site, new_forecast, new_observation):
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
    crossperm = new_permission('read', 'forecasts', False, org=org0)
    createperm = new_permission('create', 'forecasts', True, org=org0)
    forecasts0 = [new_forecast(site=site0) for _ in range(4)]
    forecasts1 = [new_forecast(site=site1) for _ in range(2)]
    forecasts2 = new_forecast(site=site0)
    obs0 = new_observation(site=site0)
    obs1 = new_observation(site=site0)
    obs2 = new_observation(site=site1)
    cursor.executemany(
        "INSERT INTO role_permission_mapping (role_id, permission_id) "
        "VALUES (%s, %s)",
        [(role0['id'], perm0['id']), (role0['id'], perm1['id']),
         (role1['id'], perm2['id']), (role2['id'], crossperm['id']),
         (role0['id'], createperm['id']), (role1['id'], createperm['id'])])
    cursor.executemany(
        "INSERT INTO permission_object_mapping (permission_id, object_id) "
        "VALUES (%s, %s)", [(perm0['id'], forecasts0[0]['id']),
                            (perm0['id'], forecasts0[1]['id']),
                            (perm1['id'], forecasts0[2]['id']),
                            (perm1['id'], forecasts0[3]['id']),
                            (crossperm['id'], forecasts2['id'])])
    return ((org0, org1), (user0, user1), (role0, role1, role2),
            (site0, site1),
            (perm0, perm1, perm2, crossperm, createperm),
            forecasts0 + forecasts1 + [forecasts2],
            (obs0, obs1, obs2))


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
