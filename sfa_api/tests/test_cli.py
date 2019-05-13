import tempfile


from click.testing import CliRunner

import sfa_api
from sfa_api import cli


def test_worker(mocker):
    w = mocker.patch('rq.Worker')
    runner = CliRunner()
    with tempfile.NamedTemporaryFile('r') as f:
        r = runner.invoke(cli.cli, ['worker', f.name])
    assert r.exit_code == 0
    w.assert_called


def test_devserver(mocker):
    app = mocker.patch.object(sfa_api, 'create_app')
    runner = CliRunner()
    r = runner.invoke(cli.cli, ['devserver'])
    assert r.exit_code == 0
    app.assert_called
