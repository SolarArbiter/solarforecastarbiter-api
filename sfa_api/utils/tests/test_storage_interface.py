import uuid


import pytest
import pymysql


from sfa_api import create_app
from sfa_api.demo.sites import static_sites as demo_sites
from sfa_api.utils import storage_interface


@pytest.fixture(scope='module')
def app():
    app = create_app('TestingConfig')
    with app.app_context():
        try:
            storage_interface.mysql_connection()
        except pymysql.err.OperationalError:
            pytest.skip('No connection to test database')
        else:
            yield app


@pytest.fixture(scope='module')
def user(app):
    ctx = app.test_request_context()
    ctx.user = 'auth0|testtesttest'
    ctx.push()
    yield
    ctx.pop()


@pytest.fixture(scope='module')
def invalid_user(app):
    ctx = app.test_request_context()
    ctx.user = 'bad'
    ctx.push()
    yield
    ctx.pop()


def test_get_cursor_and_timezone(app):
    with storage_interface.get_cursor() as cursor:
        cursor.execute('SELECT @@session.time_zone')
        res = cursor.fetchone()[0]
    assert res == '+00:00'


@pytest.mark.parametrize('site_id', demo_sites.keys())
def test_read_site(app, user, site_id):
    site = storage_interface.read_site(site_id)
    assert site == demo_sites[site_id]


def test_read_invalid_site(app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_site(str(uuid.uuid1()))


def test_read_invalid_user(app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_site(list(demo_sites.keys())[0])


def test_list_sites(app, user):
    sites = storage_interface.list_sites()
    for site in sites:
        assert site == demo_sites[site['site_id']]


def test_list_invalid_user(app, invalid_user):
    sites = storage_interface.list_sites()
    assert len(sites) == 0
