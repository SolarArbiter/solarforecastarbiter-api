from pathlib import Path
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics


bind = '127.0.0.1:8080'
workers = 8
worker_class = 'gevent'
keep_alive = 5
ssl_version = 5
certfile = '/certs/tls.crt' if Path('/certs/tls.crt').exists() else None
keyfile = '/certs/tls.key' if Path('/certs/tls.key').exists() else None
# date X-Forwarded-For status "status line" response_length "referer" "user agent" request_time (s)  # NOQA
access_log_format = '%(t)s %({X-Forwarded-For}i)s %(s)s "%(r)s" %(b)s "%(f)s" "%(a)s"  %(L)s'  # NOQA
accesslog = '-'


def when_ready(server):
    GunicornPrometheusMetrics.start_http_server_when_ready(8081)


def child_exit(server, worker):
    GunicornPrometheusMetrics.mark_process_dead_on_child_exit(worker.pid)
