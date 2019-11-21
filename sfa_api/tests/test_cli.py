import tempfile


from click.testing import CliRunner
import pytest


import sfa_api
from sfa_api import cli


@pytest.mark.parametrize('args', [
    ['-v'],
    ['-vv'],
    ['-q one', '-q two'],
    ['-v', '-q default'],
])
def test_worker(mocker, args):
    w = mocker.patch('rq.Worker')
    runner = CliRunner()
    with tempfile.NamedTemporaryFile('r') as f:
        r = runner.invoke(cli.cli, ['worker', *args, f.name])
    assert r.exit_code == 0
    w.assert_called


def test_devserver(mocker):
    app = mocker.patch.object(sfa_api, 'create_app')
    runner = CliRunner()
    r = runner.invoke(cli.cli, ['devserver'])
    assert r.exit_code == 0
    app.assert_called


def test_scheduled_worker(mocker):
    w = mocker.patch('rq.Worker')
    runner = CliRunner()
    with tempfile.NamedTemporaryFile('w') as f:
        f.write('SCHEDULER_QUEUE = "scheduled"')
        f.flush()
        r = runner.invoke(cli.cli, ['scheduled-worker', f.name])
    assert r.exit_code == 0
    w.assert_called


def test_scheduler(mocker):
    run = mocker.patch('rq_scheduler.Scheduler.run')
    runner = CliRunner()
    with tempfile.NamedTemporaryFile('w') as f:
        f.write('USE_FAKE_REDIS = True\n')
        f.write('SCHEDULER_QUEUE = "scheduled"')
        f.flush()
        r = runner.invoke(cli.cli, ['scheduler', f.name])
    assert r.exit_code == 0
    run.assert_called
