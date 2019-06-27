from flask import current_app
import pytest
from redis import Redis
from rq import Queue


from sfa_api.utils import queuing


def test_make_redis_connection(demo_app):
    with demo_app.app_context():
        r = queuing.make_redis_connection(current_app.config)
    assert isinstance(r, Redis)


@pytest.mark.parametrize('name', ['default', 'reports'])
def test_get_queue_real(mocker, demo_app, name):
    mocked = mocker.patch.object(queuing, 'make_redis_connection')
    with demo_app.app_context():
        current_app.config['USE_FAKE_REDIS'] = False
        q = queuing.get_queue(name)
    assert isinstance(q, Queue)
    assert q.name == name
    assert mocked.called


@pytest.mark.parametrize('name', ['default', 'reports'])
def test_get_queue_fake(mocker, demo_app, name):
    mocked = mocker.patch('fakeredis.FakeStrictRedis')
    with demo_app.app_context():
        current_app.config['USE_FAKE_REDIS'] = True
        q = queuing.get_queue(name)
    assert isinstance(q, Queue)
    assert q.name == name
    assert mocked.called
