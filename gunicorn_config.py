import os
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics


bind = '127.0.0.1:8080'
workers = 8
worker_class = 'gevent'
keep_alive = 5
if not os.getenv('SFAAPI_INSECURE', False):
    ssl_version = 5
    certfile = '/certs/tls.crt'
    keyfile = '/certs/tls.key'
# remote_address - user date "status line" status response_length "referer" "user agent" "X-Forwarded-For" request_time (s)  # NOQA
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" "%({X-Forwarded-For}i)s" %(L)s'  # NOQA
accesslog = '-'


def when_ready(server):
    GunicornPrometheusMetrics.start_http_server_when_ready(8081)


def child_exit(server, worker):
    GunicornPrometheusMetrics.mark_process_dead_on_child_exit(worker.pid)
