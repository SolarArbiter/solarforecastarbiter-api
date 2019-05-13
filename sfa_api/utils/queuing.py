from flask import current_app
from redis import Redis
from rq import Queue


def make_redis_connection(config):
    """Make a connection to the Redis configuration provided in config"""
    host = config.get('REDIS_HOST', '127.0.0.1')
    port = int(config.get('REDIS_PORT', '6379'))
    db = config.get('REDIS_DB', 0)
    passwd = config.get('REDIS_PASSWORD', None)
    socket_timeout = config.get('REDIS_SOCKET_TIMEOUT', 60)
    socket_connect_timeout = config.get('REDIS_SOCKET_CONNECT_TIMEOUT', 15)
    ssl = config.get('REDIS_USE_SSL', False)
    ssl_ca_certs = config.get(
        'REDIS_CA_CERTS',
        '/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt')
    r = Redis(host=host, port=port, db=db, password=passwd,
              socket_timeout=socket_timeout,
              socket_connect_timeout=socket_connect_timeout,
              ssl=ssl, ssl_ca_certs=ssl_ca_certs)
    return r


def get_queue():
    """Return the background task queue"""
    if not hasattr(current_app, 'background_queue'):
        if current_app.config.get('USE_FAKE_REDIS', False):
            from fakeredis import FakeStrictRedis
            current_app.background_queue = Queue(
                is_async=False, connection=FakeStrictRedis())
        else:
            redis_conn = make_redis_connection(current_app.config)
            current_app.background_queue = Queue(connection=redis_conn)
    return current_app.background_queue
