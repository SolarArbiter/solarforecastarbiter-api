"""
Required keys: TOKEN_ENCRYPTION_KEY, SCHEDULER_QUEUE, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_BASE_URL, AUTH0_AUDIENCE, MYSQL_HOST, MYSQL_DATABASE, MYSQL_PASSWORD, MYSQL_USER
optional: REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
REDIS_DECODE_RESPONSES, REDIS_SOCKET_CONNECT_TIMEOUT,
REDIS_USE_SSL, REDIS_CA_CERTS, REDIS_CERT_REQS,
LOG_LEVEL
"""
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


def get_access_token(user_id):
    """requires app context"""
    try:
        enc_token = storage._call_procedure(
            'fetch_token', (user_id,), with_current_user=False,
        )[0]['token'].encode()
    except IndexError:
        raise KeyError(f'No token for {user_id} found')
    f = Fernet(current_app.config['TOKEN_ENCRYPTION_KEY'])
    refresh_token = f.decrypt(enc_token)
    access_token = exchange_refresh_token(refresh_token)
    return HiddenToken(access_token)


def utcnow():
    return pd.Timestamp.now(tz='UTC')


def create_job(job_type, name, user_id, cron_string, **kwargs):
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
        'store_job', (id_, user_id, name, job_type, json.dumps(params),
                      json.dumps(schedule), 0))
    return id_


def execute_job(name, job_type, user_id, **kwargs):
    logger.info('Running job %s of type %s', name, job_type)
    token = get_access_token(user_id)
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
    args = [sql_job[k] for k in ('name', 'job_type', 'user_id')]
    kwargs = json.loads(sql_job['parameters'])
    schedule = json.loads(sql_job['schedule'])
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
    logger.debug('Syncing MySQL and RQ jobs...')
    sql_jobs = storage._call_procedure('list_jobs', (None, ),
                                       with_current_user=False)
    rq_jobs = scheduler.get_jobs()

    sql_dict = {k['id']: k for k in sql_jobs}
    rq_dict = {j.id: j for j in rq_jobs}

    for to_cancel in set(rq_dict.keys()) - set(sql_dict.keys()):
        logger.info('Removing extra RQ jobs %s',
                    rq_dict[to_cancel].meta.get('job_name', to_cancel))
        scheduler.cancel(to_cancel)

    for job_id, sql_job in sql_dict.items():
        if job_id in rq_dict:
            if (
                    sql_job['modified_at'] !=
                    rq_dict[job_id].meta['last_modified_in_sql']
            ):
                logger.info('Removing job %s', sql_job['name'])
                scheduler.cancel(job_id)
            else:
                continue
        try:
            convert_sql_to_rq_job(sql_job, scheduler)
        except (ValueError, json.JSONDecodeError, KeyError) as e:
            logger.error(
                'Failed to schedule job %s with error %s',
                sql_job, e)


@contextmanager
def make_job_app(config_file):
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
