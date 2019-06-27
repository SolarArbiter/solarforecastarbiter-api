from flask import current_app
from redis import Redis
from rq import Queue


def make_redis_connection(config):
    """Make a connection to the Redis configuration provided in config"""
    host = config.get('REDIS_HOST', '127.0.0.1')
    port = int(config.get('REDIS_PORT', '6379'))
    db = config.get('REDIS_DB', 0)
    passwd = config.get('REDIS_PASSWORD', None)
    socket_connect_timeout = config.get('REDIS_SOCKET_CONNECT_TIMEOUT', 15)
    ssl = config.get('REDIS_USE_SSL', False)
    ssl_ca_certs = config.get(
        'REDIS_CA_CERTS',
        '/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt')
    ssl_cert_reqs = config.get('REDIS_CERT_REQS', 'required')
    r = Redis(host=host, port=port, db=db, password=passwd,
              socket_connect_timeout=socket_connect_timeout,
              ssl=ssl, ssl_ca_certs=ssl_ca_certs,
              ssl_cert_reqs=ssl_cert_reqs)
    return r


def get_queue(qname='default'):
    """Return the requested task queue"""
    # start with queue_ so they are grouped together on app
    # for debugging later
    app_qname = f'queue_{qname}'
    if not hasattr(current_app, app_qname):
        if current_app.config.get('USE_FAKE_REDIS', False):
            from fakeredis import FakeStrictRedis
            q = Queue(qname, is_async=False, connection=FakeStrictRedis())
        else:
            redis_conn = make_redis_connection(current_app.config)
            q = Queue(qname, connection=redis_conn)
        setattr(current_app, app_qname, q)
    return getattr(current_app, app_qname)
