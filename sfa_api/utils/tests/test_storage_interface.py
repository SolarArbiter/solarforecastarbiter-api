import pytest
import pymysql


from sfa_api import create_app
from sfa_api.utils import storage_interface


@pytest.fixture(scope='module')
def app():
    app = create_app('DevelopmentConfig')
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


def test_get_cursor(app):
    with storage_interface.get_cursor() as cursor:
        cursor.execute('SELECT @@session.time_zone')
        res = cursor.fetchone()[0]
    assert res


def test_list_sites(app, user):
    sites = storage_interface.list_sites()
    assert len(sites) > 0
    # should compare against demo?
