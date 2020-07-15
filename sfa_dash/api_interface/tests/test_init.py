from pathlib import Path
import socket
import subprocess


import time


import pytest
import requests


from sfa_dash import api_interface


@pytest.fixture()
def context(app, client):
    with app.app_context():
        client.get('')
        yield app


@pytest.fixture()
def background_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    app_path = Path(__file__).parent / 'app.py'
    proc = subprocess.Popen(
        ['python', str(app_path.absolute()), str(port)],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)
    addr = f'http://127.0.0.1:{port}'
    i = 0
    while i < 10:
        try:
            requests.get(addr + '/ping')
        except Exception:
            i += 1
            time.sleep(0.5)
        else:
            break
    yield addr
    proc.kill()


def test_get_request(context, background_server):
    context.config['SFA_API_URL'] = background_server
    req = api_interface.get_request('/ok')
    assert req == 'ok'


def test_get_request_405(context, background_server):
    context.config['SFA_API_URL'] = background_server
    with pytest.raises(requests.exceptions.HTTPError):
        api_interface.get_request('/badreq')


def test_get_request_500(context, background_server):
    context.config['SFA_API_URL'] = background_server
    with pytest.raises(requests.exceptions.HTTPError):
        api_interface.get_request('/err')


def test_get_request_one_503(context, background_server):
    context.config['SFA_API_URL'] = background_server
    req = api_interface.get_request('/')
    assert req == 'OK'


def test_background_server_works(background_server):
    r1 = requests.get(background_server + '/')
    r2 = requests.get(background_server + '/')
    assert r1.status_code == 503
    assert r2.text == 'OK'
    with pytest.raises(requests.exceptions.ChunkedEncodingError):
        requests.get(background_server + '/length')
    requests.get(background_server + '/length').text == 'OK'


def test_bad_length(context, background_server):
    context.config['SFA_API_URL'] = background_server
    req = api_interface.get_request('/length')
    assert req == 'OK'


def test_bad_length_retries_exhausted(context, background_server):
    context.config['SFA_API_URL'] = background_server
    with pytest.raises(requests.exceptions.ChunkedEncodingError):
        api_interface.get_request('/alwaysfail')
