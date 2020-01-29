from contextlib import contextmanager
import json
import logging


from cryptography.fernet import Fernet
from flask import current_app, Flask
import pandas as pd
from solarforecastarbiter.io import nwp
from solarforecastarbiter.io.utils import HiddenToken
from solarforecastarbiter.reference_forecasts.main import make_latest_nwp_forecasts  # NOQA
from solarforecastarbiter.reports.main import compute_report
from solarforecastarbiter.validation.tasks import daily_observation_validation


from sfa_api.utils.auth0_info import exchange_refresh_token
from sfa_api.utils.queuing import get_queue
import sfa_api.utils.storage_interface as storage


logger = logging.getLogger(__name__)


def exchange_token(user_id):
    """
    Get the refresh token from MySQL for the user_id, decrypt it, and
    exchange it for an access token. This requires the same
    TOKEN_ENCRYPTION_KEY that was used to encrypt the token along with
    the same AUTH0_CLIENT_ID and AUTH0_CLIENT_SECRET to do anything
    useful with the refresh token.

    Parameters
    ----------
    user_id : str
        Retrieve an access token for this user

    Returns
    -------
    HiddenToken
        The access token that can be accessed at the .token property

    Raises
    ------
    KeyError
        If no token is found for user_id
    """
    try:
        enc_token = storage._call_procedure(
            'fetch_token', (user_id,), with_current_user=False,
        )[0]['token'].encode()
    except IndexError:
        raise KeyError(f'No token for {user_id} found')
    f = Fernet(current_app.config['TOKEN_ENCRYPTION_KEY'])
    refresh_token = f.decrypt(enc_token).decode()
    access_token = exchange_refresh_token(refresh_token)
    return HiddenToken(access_token)


def create_job(job_type, name, user_id, cron_string, **kwargs):
    """
    Create a job in the database

    Parameters
    ----------
    job_type : str
        Type of background job. This determines what kwargs are expected
    name : str
        Name for the job
    user_id : str
        ID of the user to execute this job
    cron_string : str
        Crontab string to schedule job
    **kwargs
        Keyword arguments that will be passed along when the job is executed

    Returns
    -------
    str
        ID of the MySQL job

    Raises
    ------
    ValueError
        If the job type is not supported
    """
    logger.info('Creating %s job', job_type)

    if job_type == 'daily_observation_validation':
        keys = ('start_td', 'end_td')
    elif job_type == 'reference_nwp':
        keys = ('issue_time_buffer',)
    elif job_type == 'periodic_report':
        # report must already exist
        keys = ('report_id',)
    else:
        raise ValueError(f'Job type {job_type} is not supported')
    params = {}
    if 'base_url' in kwargs:
        params['base_url'] = kwargs['base_url']
    for k in keys:
        params[k] = kwargs[k]

    schedule = {'type': 'cron', 'cron_string': cron_string}
    id_ = storage.generate_uuid()
    storage._call_procedure(
        'store_job', id_, str(user_id), name, job_type, json.dumps(params),
        json.dumps(schedule), 0, with_current_user=False)
    return id_


def utcnow():
    return pd.Timestamp.now(tz='UTC')


def execute_job(name, job_type, user_id, **kwargs):
    """
    Function that should be given to RQ to execute the
    proper code depending on job type

    Parameters
    ----------
    job_type : str
        The type of job to determine which code path to run
    user_id : str
        The ID of the user that this job should execute as
    **kwargs
        Additional keyword arguments passed to the execution code

    Raises
    ------
    ValueError
        If the job type is unsupported
    """
    logger.info('Running job %s of type %s', name, job_type)
    token = exchange_token(user_id)
    base_url = kwargs.get('base_url', None)
    if job_type == 'daily_observation_validation':
        start = utcnow() + pd.Timedelta(kwargs['start_td'])
        end = utcnow() + pd.Timedelta(kwargs['end_td'])
        return daily_observation_validation(token, start, end, base_url)
    elif job_type == 'reference_nwp':
        issue_buffer = pd.Timedelta(kwargs['issue_time_buffer'])
        run_time = utcnow()
        nwp.set_base_path(kwargs.get('nwp_directory', '/data'))
        return make_latest_nwp_forecasts(
            token, run_time, issue_buffer, base_url)
    elif job_type == 'periodic_report':
        return compute_report(token, kwargs['report_id'], base_url)
    else:
        raise ValueError(f'Job type {job_type} is not supported')


def convert_sql_to_rq_job(sql_job, scheduler):
    """
    Convert between a job as stored in MySQL and a job for
    RQ scheduler to execute.

    Parameters
    ----------
    sql_job : dict
        Definition of the job as returned from MySQL with keys including
        id, name, job_type, user_id, parameters, schedule, organization_id,
        modified_at
    scheduler : rq_schduler.Scheduler
        Scheduler instance where a new scheduled job will be created

    Raises
    ------
    ValueError
        If the type of scheduling is not cron
    """
    args = [sql_job[k] for k in ('name', 'job_type', 'user_id')]
    kwargs = sql_job['parameters']
    schedule = sql_job['schedule']
    if schedule['type'] != 'cron':
        raise ValueError('Only cron job schedules are supported')
    logger.info('Adding job %s with schedule %s', sql_job['name'],
                schedule['cron_string'])
    scheduler.cron(
        schedule['cron_string'],
        func=execute_job,
        args=args,
        kwargs=kwargs,
        repeat=schedule.get('repeat', None),
        id=sql_job['id'],
        meta={'sql_job': sql_job['id'],
              'job_name': sql_job['name'],
              'org': sql_job['organization_id'],
              'last_modified_in_sql': sql_job['modified_at']},
    )


def schedule_jobs(scheduler):
    """
    Sync jobs between MySQL and RQ scheduler, adding new jobs
    from MySQL, updating jobs if they have changed, and remove
    RQ jobs that have been removed from MySQL

    Parameters
    ----------
    scheduler : rq_scheduler.Scheduler
        The scheduler instance to compare MySQL jobs with
    """
    logger.debug('Syncing MySQL and RQ jobs...')
    sql_jobs = storage._call_procedure('list_jobs',
                                       with_current_user=False)
    rq_jobs = scheduler.get_jobs()

    sql_dict = {k['id']: k for k in sql_jobs}
    rq_dict = {j.id: j for j in rq_jobs}

    for to_cancel in set(rq_dict.keys()) - set(sql_dict.keys()):
        logger.info('Removing extra RQ jobs %s',
                    rq_dict[to_cancel].meta.get('job_name', to_cancel))
        scheduler.cancel(to_cancel)
        # make sure job removed from redis
        rq_dict[to_cancel].delete()

    for job_id, sql_job in sql_dict.items():
        if job_id in rq_dict:
            if (
                    sql_job['modified_at'] !=
                    rq_dict[job_id].meta['last_modified_in_sql']
            ):
                logger.info('Removing job %s', sql_job['name'])
                scheduler.cancel(job_id)
            else:
                continue  # pragma: no cover
        try:
            convert_sql_to_rq_job(sql_job, scheduler)
        except (ValueError, json.JSONDecodeError, KeyError) as e:
            logger.error(
                'Failed to schedule job %s with error %s',
                sql_job, e)


@contextmanager
def make_job_app(config_file):
    """
    Context-manager to make a Flask app and RQ Queue for running the RQ
    scheduler and workers

    Parameters
    ----------
    config_file : file-path
        Path to a python configuration file. Important parameters include
        the Redis connection keys, the Auth0 connection parameters, and
        the MySQL connection parameters.

    Yields
    ------
    app
        The Flask app, which has a running context for access to
        flask.current_app
    queue
        The RQ queue, using app.config['SCHEDULER_QUEUE'], with an active
        Redis connection
    """
    app = Flask('scheduled_jobs')
    app.config.from_pyfile(config_file)
    with app.app_context():
        queue = get_queue(app.config['SCHEDULER_QUEUE'])
        yield app, queue


class UpdateMixin:
    """
    Simple Mixin for rq_scheduler.Scheduler to sync SQL and RQ jobs
    each time the Scheduler moves jobs to the run queue.
    """
    def enqueue_jobs(self):
        schedule_jobs(self)
        return super().enqueue_jobs()
