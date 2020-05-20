import logging
from pathlib import Path


import click
from flask import Config
import sentry_sdk


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass


verbose_opt = click.option('-v', '--verbose', count=True,
                           help='Increase logging verbosity')
worker_ttl = click.option(
    '--worker-ttl', default=420,
    help='The timeout for the worker monitoring process'
)
job_monitoring_interval = click.option(
    '--job-monitoring-interval', default=30,
    help='The timeout for an individual job running in a work-horse process'
)


def _get_log_level(config, verbose, key='LOG_LEVEL'):  # pragma: no cover
    if key in config:
        loglevel = config[key]
    else:
        if verbose == 1:
            loglevel = 'INFO'
        elif verbose > 1:
            loglevel = 'DEBUG'
        else:
            loglevel = 'WARNING'
    return loglevel


def _setup_logging(level):
    root_logger = logging.getLogger()
    formatter = logging.Formatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


@cli.command()
@verbose_opt
@click.option('-q', '--queues', multiple=True, help='RQ queues',
              default=['default'])
@worker_ttl
@job_monitoring_interval
@click.argument('config_file')
def worker(verbose, queues, worker_ttl, job_monitoring_interval, config_file):
    """
    Run an RQ worker, with config loaded from CONFIG_FILE,
    to process commands on the QUEUES.
    """
    from sentry_sdk.integrations.rq import RqIntegration
    sentry_sdk.init(send_default_pii=False,
                    integrations=[RqIntegration()])

    from rq import Connection, Worker
    import solarforecastarbiter  # NOQA preload
    from sfa_api.utils.queuing import make_redis_connection

    config = Config(Path.cwd())
    config.from_pyfile(config_file)

    worker_loglevel = _get_log_level(config, verbose, key='WORKER_LOG_LEVEL')
    _setup_logging(_get_log_level(config, verbose))

    if 'QUEUES' in config:  # pragma: no cover
        queues = config['QUEUES']

    # will likely want to add prometheus in here somewhere,
    # perhaps as custom worker class
    # if possible, get len report obj, time range
    red = make_redis_connection(config)
    with Connection(red):
        w = Worker(queues,
                   default_worker_ttl=worker_ttl,
                   job_monitoring_interval=job_monitoring_interval)
        w.work(logging_level=worker_loglevel)


@cli.command()
@click.option('-p', '--port', type=int, help='Port for the server to run on',
              default=5000)
@click.argument('config_name', required=False,
                default='DevelopmentConfig')
def devserver(port, config_name):
    """Run a flask development server with config from CONFIG_NAME"""
    from sfa_api import create_app
    app = create_app(config_name)
    app.run(port=port)


@cli.command()
@verbose_opt
@click.argument('config_file')
@worker_ttl
@job_monitoring_interval
def scheduled_worker(
        verbose, config_file, worker_ttl, job_monitoring_interval):
    """
    Run an RQ worker for use with scheduled jobs, with config loaded
    from CONFIG_FILE.
    """
    from sentry_sdk.integrations.rq import RqIntegration
    sentry_sdk.init(send_default_pii=False,
                    integrations=[RqIntegration()])
    from rq import Worker
    from sfa_api.jobs import make_job_app
    import solarforecastarbiter  # NOQA preload

    with make_job_app(config_file) as (app, queue):
        worker_loglevel = _get_log_level(
            app.config, verbose, key='WORKER_LOG_LEVEL')
        _setup_logging(_get_log_level(app.config, verbose))
        w = Worker(queue, connection=queue.connection,
                   default_worker_ttl=worker_ttl,
                   job_monitoring_interval=job_monitoring_interval)
        w.work(logging_level=worker_loglevel)


@cli.command()
@verbose_opt
@click.option('--interval', help='Interval to move scheduled jobs to queue',
              default=60.0)
@click.option('--burst', help='Move jobs once and exit',
              default=False)
@click.argument('config_file')
def scheduler(verbose, config_file, interval, burst):
    """
    Run an RQ scheduler to send work on a schedule with config
    loaded from CONFIG_FILE
    """
    from sentry_sdk.integrations.rq import RqIntegration
    sentry_sdk.init(send_default_pii=False,
                    integrations=[RqIntegration()])
    from rq_scheduler import Scheduler
    from sfa_api.jobs import make_job_app, UpdateMixin
    import solarforecastarbiter  # NOQA preload

    class UpdateScheduler(UpdateMixin, Scheduler):
        pass

    with make_job_app(config_file) as (app, queue):
        loglevel = _get_log_level(app.config, verbose)
        _setup_logging(loglevel)
        scheduler = UpdateScheduler(queue=queue, interval=interval,
                                    connection=queue.connection)
        scheduler.run(burst=burst)


if __name__ == '__main__':  # pragma: no cover
    cli()
