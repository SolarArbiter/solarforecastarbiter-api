import pytest
from requests.exceptions import HTTPError


from sfa_dash.api_interface.util import handle_response
from sfa_dash.errors import DataRequestException


@pytest.fixture()
def mock_response(mocker):
    def fn(status_code):
        def raise_for():
            raise HTTPError()
        resp = mocker.Mock()
        resp.status_code = status_code
        resp.ok = False
        resp.json = lambda: {'errors': {str(status_code): 'error'}}
        resp.raise_for_status = raise_for
        return resp
    return fn


@pytest.fixture()
def mock_request(mocker):
    mocker.patch('sfa_dash.api_interface.util.request')


@pytest.mark.parametrize('code', [
    400, 401, 404, 422])
def test_handle_response_requesterror(mock_response, code, mock_request):
    with pytest.raises(DataRequestException):
        handle_response(mock_response(code))


@pytest.mark.parametrize('code', [500, 502, 504])
def test_handle_response_requesterror_500(mock_response, code, mock_request):
    with pytest.raises(HTTPError):
        handle_response(mock_response(code))
