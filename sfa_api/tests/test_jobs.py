import datetime as dt
import tempfile


import pytest
from rq import SimpleWorker
from rq_scheduler import Scheduler


from sfa_api import jobs
from sfa_api.utils.queuing import get_queue
from sfa_api.conftest import _make_sql_app, _make_nocommit_cursor


@pytest.fixture()
def app(mocker):
    with _make_sql_app() as app:
        app.config.update(
            TOKEN_ENCRYPTION_KEY=b'eKfeo832hn8nQ_3K69YDniBbHqbqpIxUNRstrv225c8=',  # NOQA
            SCHEDULER_QUEUE='scheduler',
            MYSQL_USER='job_executor',
            MYSQL_PASSWORD='thisisaterribleandpublicpassword'
        )
        with _make_nocommit_cursor(mocker):
            yield app


@pytest.fixture()
def queue(app):
    return get_queue(app.config['SCHEDULER_QUEUE'])


def test_exchange_token(mocker, app, userid):
    exchange = mocker.patch('sfa_api.jobs.exchange_refresh_token',
                            return_value='access')
    out = jobs.exchange_token(userid)
    assert out.token == 'access'
    assert exchange.called_with('token')


def test_exchange_token_dne(app):
    with pytest.raises(KeyError):
        jobs.exchange_token('1190950a-7cca-11e9-a81f-54bf64606445')


def test_make_job_app(mocker):
    with tempfile.NamedTemporaryFile(mode='w') as f:
        f.write('SCHEDULER_QUEUE = "scheduled_jobsq"')
        f.flush()

        with jobs.make_job_app(f.name) as (app, queue):
            assert queue.name == 'scheduled_jobsq'


def test_schedule_jobs(mocker, queue, jobid):
    sch = Scheduler(queue=queue, connection=queue.connection)
    sch.cancel = mocker.MagicMock()
    jobs.schedule_jobs(sch)
    assert jobid in sch
    assert len(list(sch.get_jobs())) == 1
    # running again should have no effect
    jobs.schedule_jobs(sch)
    assert jobid in sch
    assert len(list(sch.get_jobs())) == 1
    assert not sch.cancel.called


def noop():
    pass


def test_schedule_jobs_bad_current(mocker, queue, jobid):
    sch = Scheduler(queue=queue, connection=queue.connection)
    id0 = 'jobid0'
    sch.cron(
        '* * * * *',
        func=noop,
        id=id0,
        meta={}
    )
    jobs.schedule_jobs(sch)
    assert jobid in sch
    assert id0 not in sch
    assert len(list(sch.get_jobs())) == 1


@pytest.fixture()
def sql_job(userid, orgid, jobid):
    return {
        'id': jobid,
        'user_id': userid,
        'organization_id': orgid,
        'name': 'Test job',
        'job_type': 'daily_observation_validation',
        'parameters': {
            "start_td": "-1d",
            "end_td": "0h",
            "base_url": "http://localhost:5000"
        },
        'schedule': {"type": "cron", "cron_string": "0 0 * * *"},
        'version': 0,
        'created_at': dt.datetime(2019, 1, 1, 12, tzinfo=dt.timezone.utc),
        'modified_at': dt.datetime(2019, 1, 1, 12, tzinfo=dt.timezone.utc)
    }


def test_schedule_jobs_modified(mocker, queue, sql_job):
    mocker.patch('sfa_api.jobs.storage._call_procedure',
                 return_value=[sql_job])
    sch = Scheduler(queue=queue, connection=queue.connection)
    jobs.schedule_jobs(sch)
    assert list(sch.get_jobs())[0].meta[
        'last_modified_in_sql'] == dt.datetime(2019, 1, 1, 12,
                                               tzinfo=dt.timezone.utc)
    njob = sql_job.copy()
    njob['modified_at'] = dt.datetime(2019, 2, 1, tzinfo=dt.timezone.utc)
    mocker.patch('sfa_api.jobs.storage._call_procedure',
                 return_value=[njob])
    jobs.schedule_jobs(sch)
    assert list(sch.get_jobs())[0].meta[
        'last_modified_in_sql'] == dt.datetime(
            2019, 2, 1, tzinfo=dt.timezone.utc)


def test_schedule_jobs_err(mocker, queue, sql_job):
    job = sql_job.copy()
    job['schedule'] = {}
    mocker.patch('sfa_api.jobs.storage._call_procedure',
                 return_value=[job])
    log = mocker.patch('sfa_api.jobs.logger')
    sch = Scheduler(queue=queue, connection=queue.connection)
    jobs.schedule_jobs(sch)
    assert log.error.called


def test_convert_sql_job_to_rq_job(sql_job, mocker):
    scheduler = mocker.MagicMock()
    jobs.convert_sql_to_rq_job(sql_job, scheduler)
    assert scheduler.cron.called
    assert scheduler.cron.call_args[0] == ('0 0 * * *',)


def test_convert_sql_job_to_rq_job_not_cron(sql_job, mocker):
    job = sql_job.copy()
    job['schedule'] = {"type": "enqueue_at"}
    scheduler = mocker.MagicMock()
    with pytest.raises(ValueError):
        jobs.convert_sql_to_rq_job(job, scheduler)


@pytest.mark.parametrize('jtype,params,func', [
    ('daily_observation_validation',
     {'start_td': '-1h', 'end_td': '0h'},
     'sfa_api.jobs.daily_observation_validation'),
    ('reference_nwp',
     {'issue_time_buffer': '10min',
      'nwp_directory': '.'},
     'sfa_api.jobs.make_latest_nwp_forecasts'),
    ('periodic_report',
     {'report_id': 'blah'},
     'sfa_api.jobs.compute_report'),
    pytest.param(
        'other_job', {}, 'sfa_api.app',
        marks=pytest.mark.xfail(strict=True, raises=ValueError))
])
def test_execute_job_daily_obs(jtype, params, func, mocker, userid):
    mocker.patch('sfa_api.jobs.exchange_token',
                 return_value='token')
    ret = mocker.patch(func)
    jobs.execute_job('test', jtype, userid, **params)
    assert ret.called


def test_full_run_through(app, queue, mocker):
    mocker.patch('sfa_api.jobs.exchange_token', return_value='token')
    validate = mocker.patch('sfa_api.jobs.daily_observation_validation')
    gjq = mocker.patch('rq_scheduler.Scheduler.get_jobs_to_queue')

    class US(jobs.UpdateMixin, Scheduler):
        pass

    sch = US(queue=queue, connection=queue.connection)
    jobs.schedule_jobs(sch)
    (job, exc_time) = list(sch.get_jobs(with_times=True))[0]
    assert exc_time == dt.datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(days=1)
    gjq.return_value = [job]
    sch.run(burst=True)
    assert job in queue.jobs
    w = SimpleWorker([queue], connection=queue.connection)
    w.work(burst=True)
    assert validate.called


@pytest.fixture()
def adminapp(mocker):
    with _make_sql_app() as app:
        app.config.update(
            MYSQL_USER='frameworkadmin',
            MYSQL_PASSWORD='thisisaterribleandpublicpassword'
        )
        with _make_nocommit_cursor(mocker):
            yield app


@pytest.mark.parametrize('jt,kwargs', [
    ('daily_observation_validation', {'start_td': '1h', 'end_td': '1h'}),
    ('reference_nwp', {'issue_time_buffer': '1h', 'base_url': 'hhtp'}),
    ('periodic_report', {'report_id': 'id'}),
    pytest.param('badtype', {}, marks=pytest.mark.xfail(
        strict=True, raises=ValueError)),
    pytest.param('daily_observation_validation', {}, marks=pytest.mark.xfail(
        strict=True, raises=KeyError))
])
def test_create_job(adminapp, jt, kwargs, nocommit_cursor, user_id):
    jobs.create_job(jt, 'testcreatejob', user_id, 'cronstr', **kwargs)
    jlist = jobs.storage._call_procedure('list_jobs', with_current_user=False)
    assert len(jlist) == 2
    job = [j for j in jlist if j['name'] == 'testcreatejob'][0]
    assert job['schedule'] == {'type': 'cron', 'cron_string': 'cronstr'}
    assert job['job_type'] == jt
    assert job['parameters'] == kwargs
