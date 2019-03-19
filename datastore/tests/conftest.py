from uuid import uuid1


import pytest
import pymysql


@pytest.fixture(scope='session')
def connection():
    connection = pymysql.connect(host='127.0.0.1',
                                 port=3306,
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


def uuid_to_bin(uuid):
    """Copy mysql UUID_TO_BIN with time swap of hi and low"""
    return uuid.bytes[6:8] + uuid.bytes[4:6] + uuid.bytes[:4] + uuid.bytes[8:]


def newuuid():
    return uuid_to_bin(uuid1())


ORGANIZATIONS = [(newuuid(), f'org{i}') for i in range(2)]
USERS = [(newuuid(), f'authid{i}', org[0])
         for i, org in enumerate(ORGANIZATIONS)]
ROLES = [(newuuid(), f'role{i}', f'org{i} role', org[0])
         for i, org in enumerate(ORGANIZATIONS)]
ROLES += [(newuuid(), 'role2', 'limited read from org0',
           ORGANIZATIONS[0][0])]
USER_ROLE_MAP = [(USERS[0][0], ROLES[0][0]), (USERS[1][0], ROLES[1][0]),
                 (USERS[1][0], ROLES[2][0])]

SITES = [(newuuid(), org[0], f'site{i}')
         for i, org in enumerate(ORGANIZATIONS)]

READ_PERMISSIONS = [(newuuid(), 'Read org0 fx group 1', ORGANIZATIONS[0][0],
                     'read', 'forecasts', False),
                    (newuuid(), 'Read org0 fx group 2', ORGANIZATIONS[0][0],
                     'read', 'forecasts', False),
                    (newuuid(), 'Read org1 all fx', ORGANIZATIONS[1][0],
                     'read', 'forecasts', True),
                    (newuuid(), 'Read org0 fx 0', ORGANIZATIONS[0][0],
                     'read', 'forecasts', False)]
CREATE_PERMISSIONS = [(newuuid(), 'Create fx org0', ORGANIZATIONS[0][0],
                       'create', 'forecasts', True)]
PERMISSIONS = READ_PERMISSIONS + CREATE_PERMISSIONS
# roles, permissions, and objects must have same org! user and role do not
ROLE_PERM_MAP = [(ROLES[0][0], READ_PERMISSIONS[0][0]),
                 (ROLES[0][0], READ_PERMISSIONS[1][0]),
                 (ROLES[1][0], READ_PERMISSIONS[2][0]),
                 (ROLES[2][0], READ_PERMISSIONS[3][0]),
                 (ROLES[0][0], CREATE_PERMISSIONS[0][0]),
                 (ROLES[1][0], CREATE_PERMISSIONS[0][0])]  # not permitted
FX_OBJS = ([(newuuid(), ORGANIZATIONS[0][0], SITES[0][0], f'o0 fx{i}')
            for i in range(4)] +
           [(newuuid(), ORGANIZATIONS[1][0], SITES[1][0], f'o1 fx{i}')
            for i in range(4)])

OBS_OBJS = ([(newuuid(), ORGANIZATIONS[0][0], SITES[0][0], f'o0 obs{i}')
             for i in range(3)] +
            [(newuuid(), ORGANIZATIONS[1][0], SITES[1][0], f'o1 obs{i}')
             for i in range(2)])

# read_permissions[2] should automatically be added by trigger
PERM_OBJ_MAP = [(READ_PERMISSIONS[0][0], FX_OBJS[0][0]),
                (READ_PERMISSIONS[0][0], FX_OBJS[1][0]),
                (READ_PERMISSIONS[1][0], FX_OBJS[2][0]),
                (READ_PERMISSIONS[1][0], FX_OBJS[3][0]),
                (READ_PERMISSIONS[3][0], FX_OBJS[0][0])]


@pytest.fixture(scope='function')
def insertvals(cursor):
    cursor.executemany("INSERT INTO organizations (id, name) VALUES (%s, %s)",
                       ORGANIZATIONS)
    cursor.executemany(
        "INSERT INTO users (id, auth0_id, organization_id) VALUES (%s, %s, %s)", # NOQA
        USERS)
    cursor.executemany(
        "INSERT INTO roles (id, name, description, organization_id) VALUES "
        "(%s, %s, %s, %s)",
        ROLES)
    cursor.executemany(
        "INSERT INTO user_role_mapping (user_id, role_id) VALUES (%s, %s)",
        USER_ROLE_MAP)
    cursor.executemany(
        "INSERT INTO permissions (id, description, organization_id, action, "
        "object_type, applies_to_all) VALUES (%s, %s, %s, %s, %s, %s)",
        PERMISSIONS)
    cursor.executemany(
        "INSERT INTO role_permission_mapping (role_id, permission_id) "
        "VALUES (%s, %s)",
        ROLE_PERM_MAP)
    cursor.executemany(
        "INSERT INTO sites (id, organization_id, name) VALUES (%s, %s, %s)",
        SITES)
    cursor.executemany(
        "INSERT INTO forecasts (id, organization_id, site_id, name) VALUES "
        "(%s, %s, %s, %s)", FX_OBJS)
    cursor.executemany(
        "INSERT INTO observations (id, organization_id, site_id, name) VALUES "
        "(%s, %s, %s, %s)", OBS_OBJS)
    cursor.executemany(
        "INSERT INTO permission_object_mapping (permission_id, object_id) "
        "VALUES (%s, %s)", PERM_OBJ_MAP)
