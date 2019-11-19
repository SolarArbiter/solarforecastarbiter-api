"""
Required keys: TOKEN_ENCRYPTION_KEY, SCHEDULER_QUEUE, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_BASE_URL, AUTH0_AUDIENCE
optional: REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
REDIS_DECODE_RESPONSES, REDIS_SOCKET_CONNECT_TIMEOUT,
REDIS_USE_SSL, REDIS_CA_CERTS, REDIS_CERT_REQS,
LOG_LEVEL
"""
from contextlib import contextmanager
import json
import logging


from crytography.fernet import Fernet
from flask import current_app, Flask
import pandas as pd
from solarforecastarbiter.io import nwp
from solarforecastarbiter.io.utils import HiddenToken
import solarforecastarbiter.reference_forecasts.main as reference_forecasts
from solarforecastarbiter.reports.main import compute_report
from solarforecastarbiter.validation import tasks as validation_tasks


from sfa_api.utils.auth0_info import exchange_refresh_token
from sfa_api.utils.queuing import get_queue
import sfa_api.utils.storage_interface as storage


logger = logging.getLogger(__name__)


def get_access_token(user_id):
    """requires app context"""
    enc_token = storage._call_procedure_for_single(
        'fetch_token', (user_id,), with_current_user=False,
        )['token']
    f = Fernet(current_app.config['TOKEN_ENCRYPTION_KEY'])
    refresh_token = f.decrypt(enc_token)
    access_token = exchange_refresh_token(refresh_token)
    return HiddenToken(access_token)


def utcnow():
    return pd.Timestamp.now(tz='UTC')


def execute_job(name, job_type, user_id, **kwargs):
    logger.info('Running job %s', name)
    token = get_access_token(user_id)
    base_url = kwargs.get('base_url', None)
    if job_type == 'daily_observation_validation':
        start = utcnow() + pd.Timedelta(kwargs['start_td'])
        end = utcnow() + pd.Timedelta(kwargs['end_td'])
        return validation_tasks.daily_observation_validation(
            token, start, end, base_url)
    elif job_type == 'reference_nwp':
        issue_buffer = pd.Timedelta(kwargs['issue_time_buffer'])
        run_time = utcnow()
        nwp.set_base_path(kwargs['nwp_directory'])
        return reference_forecasts.make_latest_nwp_forecasts(
            token, run_time, issue_buffer, base_url)
    elif job_type == 'periodic_report':
        return compute_report(token, kwargs['report_id'], base_url)
    else:
        raise ValueError(f'Job type {job_type} is not supported')


def convert_sql_to_rq_job(sql_job, scheduler):
    args = (sql_job[k] for k in ('name', 'job_type', 'user_id'))
    kwargs = json.loads(sql_job['parameters'])
    schedule = json.loads(sql_job['schedule'])
    if schedule['type'] != 'cron':
        raise NotImplementedError('Only cron job schedules are supported')
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
        use_local_timezone=False
    )


def schedule_jobs(scheduler):
    sql_jobs = storage._call_procedure('list_jobs',
                                       with_current_user=False)
    rq_jobs = scheduler.get_jobs()

    sql_dict = {k['id']: k for k in sql_jobs}
    rq_dict = {j.id: j for j in rq_jobs}

    for to_cancel in set(rq_dict.keys()) - set(sql_dict.keys()):
        scheduler.cancel(to_cancel)

    for job_id, sql_job in sql_dict.items():
        if job_id not in rq_dict:
            convert_sql_to_rq_job(sql_job, scheduler)
        elif (
                sql_job['modified_at'] !=
                rq_dict[job_id].meta['last_modified_in_sql']
        ):
            scheduler.cancel(job_id)
            convert_sql_to_rq_job(sql_job, scheduler)


@contextmanager
def make_job_app(config_file):
    app = Flask('scheduled_jobs')
    app.config.from_pyfile(config_file)
    with app.app_context():
        queue = get_queue(app.config['SCHEDULER_QUEUE'])
        yield app, queue


def run_worker(queue, loglevel):
    from rq import Worker

    w = Worker(queue)
    w.work(logging_level=loglevel)


def run_scheduler(queue, interval, burst=False):
    from rq_scheduler import Scheduler

    scheduler = Scheduler(queue=queue, interval=interval)
    schedule_jobs(scheduler)
    scheduler.run(burst=burst)
