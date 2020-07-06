import pytest


import pandas as pd


from sfa_dash.blueprints.base import BaseView


@pytest.mark.parametrize('errors,expected', [
    ({'it': ['broke']}, '(it) broke'),
    ({'2': ['er', 'rors']}, '(2) er, rors'),
])
def test_flash_errors_formatting(mocker, app, errors, expected):
    flasher = mocker.patch('sfa_dash.blueprints.base.flash')
    with app.test_request_context():
        BaseView().flash_api_errors(errors)
    flasher.assert_called_with(expected, 'error')


@pytest.mark.parametrize('errors,expected', [
    ({'it': ['broke'], '2': ['er', 'rors']}, ('(it) broke', '(2) er, rors')),
])
def test_flash_errors_list_comp(mocker, app, errors, expected):
    flasher = mocker.patch('sfa_dash.blueprints.base.flash')
    with app.test_request_context():
        BaseView().flash_api_errors(errors)
    calls = [mocker.call(exp, 'error') for exp in expected]
    flasher.assert_has_calls(calls)


@pytest.fixture
def mocked_now(mocker):
    mocker.patch('sfa_dash.blueprints.base.pd.Timestamp.utcnow',
                 return_value=pd.Timestamp('2020-06-01T00:00Z'))


@pytest.mark.parametrize('start,end,expected_start,expected_end', [
    (pd.Timestamp('2019-06-05T00:00Z'), pd.Timestamp('2020-06-05T00:00Z'),
     pd.Timestamp('2020-05-31T00:00Z'), pd.Timestamp('2020-06-05T00:00Z')),
    (pd.Timestamp('2020-03-01T00:00Z'), pd.Timestamp('2020-03-30T00:00Z'),
     pd.Timestamp('2020-03-27T00:00Z'), pd.Timestamp('2020-03-30T00:00Z')),
    (None, None,
     pd.Timestamp('2020-05-29T00:00Z'), pd.Timestamp('2020-06-01T00:00Z')),
])
def test_parse_start_end_without_request_args(
        mocker, app, start, end, expected_start, expected_end, mocked_now):
    with app.test_request_context():
        view = BaseView()
        view.metadata = {'timerange_end': end, 'timerange_start': start}
        start_out, end_out = view.parse_start_end_from_querystring()
    assert start_out == expected_start
    assert end_out == expected_end


@pytest.mark.parametrize('start,end,expected_start,expected_end', [
    ('2019-06-05T00:00Z', '2020-06-05T00:00Z',
     pd.Timestamp('2019-06-05T00:00Z'), pd.Timestamp('2020-06-05T00:00Z')),
    ('2020-03-01T00:00Z', '2020-03-30T00:00Z',
     pd.Timestamp('2020-03-01T00:00Z'), pd.Timestamp('2020-03-30T00:00Z')),
    ('nat', 'nat',
     pd.Timestamp('2020-05-29T00:00Z'), pd.Timestamp('2020-06-01T00:00Z')),
])
def test_parse_start_end_with_request_args(
        mocker, app, start, end, expected_start, expected_end, mocked_now):
    with app.test_request_context(query_string={'end': end, 'start': start}):
        view = BaseView()
        view.metadata = {}
        start_out, end_out = view.parse_start_end_from_querystring()
    assert start_out == expected_start
    assert end_out == expected_end


@pytest.mark.parametrize('arg_key,arg_value,expected_start,expected_end', [
    ('start', '2020-05-30T00:00Z',
     pd.Timestamp('2020-05-30T00:00Z'), pd.Timestamp('2020-06-01T00:00Z')),
    ('end', '2020-03-30T00:00Z',
     pd.Timestamp('2020-03-27T00:00Z'), pd.Timestamp('2020-03-30T00:00Z')),
    ('end', '2020-06-05T00:00Z',
     pd.Timestamp('2020-05-31T00:00Z'), pd.Timestamp('2020-06-05T00:00Z')),
    ('start', 'nat',
     pd.Timestamp('2020-05-29T00:00Z'), pd.Timestamp('2020-06-01T00:00Z')),
    ('end', 'nat',
     pd.Timestamp('2020-05-29T00:00Z'), pd.Timestamp('2020-06-01T00:00Z')),

])
def test_parse_start_end_one_request_arg(
        mocker, app, arg_key, arg_value, expected_start, expected_end,
        mocked_now):
    with app.test_request_context(query_string={arg_key: arg_value}):
        view = BaseView()
        view.metadata = {}
        start_out, end_out = view.parse_start_end_from_querystring()
    assert start_out == expected_start
    assert end_out == expected_end


@pytest.mark.parametrize('bc_list,expected', [
    ([('dashboard', 'https://dashboard')],
     '/<a href="https://dashboard">dashboard</a>'),
    ([('a', 'b'), ('c', 'd'), ('e', 'f')],
     '/<a href="b">a</a>/<a href="d">c</a>/<a href="f">e</a>'),
])
def test_breadcrumb_html(app, bc_list, expected):
    with app.test_request_context():
        breadcrumb = BaseView().breadcrumb_html(bc_list)
        assert breadcrumb == expected
