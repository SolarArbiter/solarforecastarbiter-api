from functools import partial


from flask import current_app
from redis import Redis
from rq import Queue


def _make_redis_connection_partial():
    config = current_app.config
    host = config.get('REDIS_HOST', '127.0.0.1')
    port = int(config.get('REDIS_PORT', '6379'))
    db = config.get('REDIS_DB', 0)
    socket_timeout = config.get('REDIS_SOCKET_TIMEOUT', 10)
    socket_connect_timeout = config.get('REDIS_SOCKET_CONNECT_TIMEOUT', 5)
    ssl = config.get('REDIS_USE_SSL', False)
    ssl_ca_certs = config.get(
        'REDIS_CA_CERTS', '/var/run/secrets/kubernetes.io/service-ca.crt')
    getredis = partial(Redis, host=host, port=port, db=db,
                       socket_timeout=socket_timeout,
                       socket_connect_timeout=socket_connect_timeout,
                       ssl=ssl, ssl_ca_certs=ssl_ca_certs)
    return getredis


def get_queue():
    if not hasattr(current_app, 'background_queue'):
        if current_app.config.get('USE_FAKE_REDIS', False):
            from fakeredis import FakeStrictRedis
            current_app.background_queue = Queue(
                is_async=False, connection=FakeStrictRedis())
        else:
            redis = _make_redis_connection_partial()
            current_app.background_queue = Queue(connection=redis())
    return current_app.background_queue
