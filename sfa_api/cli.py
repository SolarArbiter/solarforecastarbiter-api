from pathlib import Path


import click
from flask import Config
import sentry_sdk


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass


@cli.command()
@click.option('-v', '--verbose', count=True, help='Increase logging verbosity')
@click.option('-q', '--queues', multiple=True)
@click.argument('config_file')
def worker(verbose, queues, config_file):
    from sentry_sdk.integrations.rq import RqIntegration
    sentry_sdk.init(integrations=[RqIntegration()])

    from rq import Connection, Worker
    import solarforecastarbiter  # NOQA preload
    from sfa_api.utils.queuing import make_redis_connection

    config = Config(Path.cwd())
    config.from_pyfile(config_file)

    if 'LOG_LEVEL' in config:
        loglevel = config['LOG_LEVEL']
    else:
        if verbose == 1:
            loglevel = 'INFO'
        elif verbose > 1:
            loglevel = 'DEBUG'
        else:
            loglevel = 'WARNING'

    if 'QUEUES' in config:
        queues = config['QUEUES']

    # will likely want to add prometheus in here somewhere,
    # perhaps as custom worker class
    red = make_redis_connection(config)
    with Connection(red):
        w = Worker(queues)
        w.work(logging_level=loglevel)


if __name__ == '__main__':
    cli()
