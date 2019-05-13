from flask import current_app
from redis import Redis
from rq import Queue


from sfa_api.utils import queuing


def test_make_redis_connection(demo_app):
    with demo_app.app_context():
        r = queuing.make_redis_connection(current_app.config)
    assert isinstance(r, Redis)


def test_get_queue_real(mocker, demo_app):
    mocked = mocker.patch.object(queuing, 'make_redis_connection')
    with demo_app.app_context():
        current_app.config['USE_FAKE_REDIS'] = False
        q = queuing.get_queue()
    assert isinstance(q, Queue)
    assert mocked.called


def test_get_queue_fake(mocker, demo_app):
    mocked = mocker.patch('fakeredis.FakeStrictRedis')
    with demo_app.app_context():
        current_app.config['USE_FAKE_REDIS'] = True
        q = queuing.get_queue()
    assert isinstance(q, Queue)
    assert mocked.called
