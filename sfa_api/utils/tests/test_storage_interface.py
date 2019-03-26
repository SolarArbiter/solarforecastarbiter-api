import flask
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
            with app.test_request_context() as ctx:
                ctx.user = 'auth0|5be343df7025406237820b85'
                yield app


def test_get_cursor(app):
    with storage_interface.get_cursor() as cursor:
        cursor.execute('SELECT @@session.time_zone')
        res = cursor.fetchone()[0]
    assert res


def test_list_sites(app):
    sites = storage_interface.list_sites()
    assert False
