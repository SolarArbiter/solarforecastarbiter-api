from copy import deepcopy
import hashlib
import itertools
import math


import pytest
from solarforecastarbiter import datamodel
from solarforecastarbiter.datamodel import (
    ALLOWED_CATEGORIES)


from sfa_api.conftest import (BASE_URL, demo_observations, demo_aggregates,
                              demo_forecasts, demo_group_cdf)
from sfa_api.schema import ALLOWED_METRICS


@pytest.fixture()
def new_report(api, report_post_json, mocked_queuing):
    def fn(rpj=report_post_json):
        res = api.post('/reports/',
                       base_url=BASE_URL,
                       json=rpj)
        return res.data.decode()
    return fn


def test_post_report(api, report_post_json, mocked_queuing):
    res = api.post('/reports/',
                   base_url=BASE_URL,
                   json=report_post_json)
    assert res.status_code == 201
    assert 'Location' in res.headers


def test_get_report(api, new_report):
    report_id = new_report()
    res = api.get(f'/reports/{report_id}',
                  base_url=BASE_URL)
    assert res.status_code == 200
    report = res.json
    assert 'report_id' in report
    assert 'provider' in report
    assert 'raw_report' in report
    assert 'status' in report
    assert 'created_at' in report
    assert 'modified_at' in report
    assert report['created_at'].endswith('+00:00')
    assert report['modified_at'].endswith('+00:00')


@pytest.fixture()
def make_cost_report(report_post_json):
    def make(type_):
        repdict = deepcopy(report_post_json)
        repdict['report_parameters']['object_pairs'][0]['cost'] = 'testcost'

        costsparams = {
            'constant': {
                'cost': 10.9,
                'net': False,
                'aggregation': 'mean'
            },
            'datetime': {
                'cost': [10.9, 11],
                'datetimes': ['2020-04-05T00:23Z', '2020-05-12T12:33-07:00'],
                'fill': 'forward',
                'net': False,
                'aggregation': 'mean',
                'timezone': 'Etc/GMT-5'
            },
            'timeofday': {
                'cost': [10.9, 11, 33],
                'times': ['12:00', '06:33', '14:00'],
                'fill': 'backward',
                'net': True,
                'aggregation': 'sum',
                'timezone': 'Etc/GMT-5'
            },
        }
        costsparams['errorband'] = {
            'bands': [
                {'error_range': [1, 2],
                 'cost_function': 'constant',
                 'cost_function_parameters': costsparams['constant']},
                {'error_range': ['-inf', 2],
                 'cost_function': 'constant',
                 'cost_function_parameters': costsparams['constant']},
                {'error_range': [2, 4],
                 'cost_function': 'datetime',
                 'cost_function_parameters': costsparams['datetime']},
                {'error_range': [3, math.inf],
                 'cost_function': 'timeofday',
                 'cost_function_parameters': costsparams['timeofday']},
            ]
        }
        if type_ in costsparams:
            repdict['report_parameters']['costs'] = [
                {'name': 'testcost', 'type': type_,
                 'parameters': costsparams[type_]}
            ]
        elif type_ == 'many':
            repdict['report_parameters']['costs'] = [
                {'name': 'testcost', 'type': 'errorband',
                 'parameters': costsparams['errorband']},
                {'name': 'othercost', 'type': 'timeofday',
                 'parameters': costsparams['timeofday']}
            ]
        return repdict
    return make


@pytest.fixture(
    params=['constant', 'datetime', 'timeofday', 'errorband', 'many'])
def report_post_json_cost(request, make_cost_report):
    return make_cost_report(request.param)


def test_cost_report_valid_datamodel(report_post_json_cost):
    # just verify that examples are aligned with expectations from
    # core datamodel
    for c in report_post_json_cost['report_parameters']['costs']:
        datamodel.Cost.from_dict(c)


def test_post_report_cost(api, report_post_json_cost,
                          mocked_queuing):
    res = api.post('/reports/',
                   base_url=BASE_URL,
                   json=report_post_json_cost)
    assert res.status_code == 201
    assert 'Location' in res.headers


def test_get_report_cost(api, new_report,
                         report_post_json_cost):
    report_id = new_report(report_post_json_cost)
    res = api.get(f'/reports/{report_id}',
                  base_url=BASE_URL)
    assert res.status_code == 200
    report = res.json
    assert 'report_id' in report
    assert 'provider' in report
    assert 'raw_report' in report
    assert 'status' in report
    assert 'created_at' in report
    assert 'modified_at' in report
    assert report['created_at'].endswith('+00:00')
    assert report['modified_at'].endswith('+00:00')
    assert len(report['report_parameters']['costs']) > 0


def test_get_report_dne(api, missing_id):
    res = api.get(f'/reports/{missing_id}',
                  base_url=BASE_URL)
    assert res.status_code == 404


@pytest.mark.parametrize('status, code', [
    ('complete', 204),
    ('failed', 204),
    ('completed', 400),
    ('invalid_status', 400),
])
def test_set_status(api, new_report, status, code):
    report_id = new_report()
    res = api.post(f'/reports/{report_id}/status/{status}',
                   base_url=BASE_URL)
    assert res.status_code == code


REPORT_VALUESET = [
    "['replace', 'with', 'real', 'data']",
]


@pytest.mark.parametrize('values', REPORT_VALUESET)
def test_post_report_values(api, new_report, values, report_json_w_cdf):
    report_id = new_report(report_json_w_cdf)
    object_pairs = report_json_w_cdf['report_parameters']['object_pairs']

    value_ids = []
    for op in object_pairs:
        for k in ('forecast', 'observation'):
            obj_id = op[k]
            report_values = {
                'object_id': obj_id,
                'processed_values': values,
            }
            res = api.post(f'/reports/{report_id}/values',
                           base_url=BASE_URL,
                           json=report_values)
            assert res.status_code == 201
            value_ids.append(res.data.decode())

    values_res = api.get(
        f'/reports/{report_id}',
        base_url=BASE_URL)
    report_with_values = values_res.get_json()
    out_ids = [v['id'] for v in report_with_values['values']]
    assert len(out_ids) == 2 * len(object_pairs)
    assert out_ids == value_ids


@pytest.mark.parametrize('values', REPORT_VALUESET[:1])
def test_post_report_values_bad_uuid(api, new_report, values):
    report_id = new_report()
    obj_id = 'bad_uuid'
    report_values = {
        'object_id': obj_id,
        'processed_values': values,
    }
    res = api.post(f'/reports/{report_id}/values',
                   base_url=BASE_URL,
                   json=report_values)
    assert res.status_code == 400
    expected = '{"errors":{"object_id":["Not a valid UUID."]}}\n'
    assert res.get_data(as_text=True) == expected


@pytest.mark.parametrize('values', REPORT_VALUESET)
def test_read_report_values(api, new_report, values, report_post_json):
    report_id = new_report()
    object_pairs = report_post_json['report_parameters']['object_pairs']
    obj_id = object_pairs[0]['observation']

    report_values = {
        'object_id': obj_id,
        'processed_values': values,
    }
    res = api.post(f'/reports/{report_id}/values',
                   base_url=BASE_URL,
                   json=report_values)
    assert res.status_code == 201
    value_id = res.data.decode()
    values_res = api.get(
        f'/reports/{report_id}/values',
        base_url=BASE_URL)
    report_values = values_res.get_json()
    assert isinstance(report_values, list)
    assert report_values[0]['id'] == value_id
    assert report_values[0]['processed_values'] == values


def test_post_raw_report(api, new_report, raw_report_json):
    report_id = new_report()
    res = api.post(f'/reports/{report_id}/raw',
                   base_url=BASE_URL,
                   json=raw_report_json)
    assert res.status_code == 204
    full_res = api.get(f'/reports/{report_id}',
                       base_url=BASE_URL)
    report_with_raw = full_res.get_json()
    assert report_with_raw['raw_report'] == raw_report_json


@pytest.mark.parametrize('chksum', [
    hashlib.sha256(b'asdf').hexdigest(),
    pytest.param('tooshort', marks=pytest.mark.xfail(strict=True)),
    pytest.param('bad??$', marks=pytest.mark.xfail(strict=True))
])
def test_post_raw_report_chksum(api, new_report, raw_report_json, chksum):
    report_id = new_report()
    post = raw_report_json
    post['data_checksum'] = chksum
    res = api.post(f'/reports/{report_id}/raw',
                   base_url=BASE_URL,
                   json=post)
    assert res.status_code == 204
    full_res = api.get(f'/reports/{report_id}',
                       base_url=BASE_URL)
    report_with_raw = full_res.get_json()
    assert report_with_raw['raw_report'] == post


def test_delete_report(api, new_report):
    report_id = new_report()
    res = api.get(f'/reports/{report_id}',
                  base_url=BASE_URL)
    assert res.status_code == 200
    delete = api.delete(f'/reports/{report_id}',
                        base_url=BASE_URL)
    assert delete.status_code == 204
    res = api.get(f'/reports/{report_id}',
                  base_url=BASE_URL)
    assert res.status_code == 404


def test_list_reports(api, new_report):
    new_report()
    new_report()
    new_report()
    reports = api.get('/reports/', base_url=BASE_URL)
    reports_list = reports.get_json()
    # one more as test already in db
    assert len(reports_list) == 4


metrics_list = ", ".join(list(ALLOWED_METRICS.keys()))
categories_list = ", ".join(list(ALLOWED_CATEGORIES.keys()))


@pytest.mark.parametrize('key,value,error', [
    ('name', 'r' * 70, '["Longer than maximum length 64."]'),
    ('start', 'invalid_date',
     '["Not a valid datetime."]'),
    ('end', 'invalid_date',
     '["Not a valid datetime."]'),
    ('object_pairs', '[{"wrongtuple"},{}]',
     '["Invalid type."]'),
    ('object_pairs', [{"observation": "x", "forecast": "y"}],
     '{"0":{"forecast":["Not a valid UUID."],'
     '"observation":["Not a valid UUID."]}}'),
    ('object_pairs', [{"observation": "123e4567-e89b-12d3-a456-426655440000",
                       "forecast": "123e4567-e89b-12d3-a456-426655440000",
                       "aggregate": "123e4567-e89b-12d3-a456-426655440000"}],
     '{"0":{"_schema":["Only specify one of observation or aggregate"]}}'),
    ('object_pairs', [{"forecast": "123e4567-e89b-12d3-a456-426655440000"}],
     '{"0":{"_schema":["Specify one of observation or aggregate"]}}'),
    ('filters', 'not a list',
     '["Invalid type."]'),
    ('metrics', ["bad"],
        f'{{"0":["Must be one of: {metrics_list}."]}}'),
    ('categories', ["bad"],
        f'{{"0":["Must be one of: {categories_list}."]}}'),
    ('object_pairs', [{"observation": "123e4567-e89b-12d3-a456-426655440000",
                       "forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3",
                       "cost": "nocost"}],
     '{"0":{"cost":["Must specify a \'cost\' that is present in report parameters \'costs\'"]}}'),  # NOQA: E501
    ('metrics', ['mae', 'cost'],
     '["Must specify \'costs\' parameters to calculate cost metric"]'),
    ('forecast_fill_method', 'invalid',
     '["Must be a float or one of \'drop\', \'forward\'"]')
])
def test_post_report_invalid_report_params(
        api, key, value, error, report_post_json):
    payload = deepcopy(report_post_json)
    payload['report_parameters'][key] = value
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    expected = ('{"errors":{"report_parameters":[{"%s":%s}]}}\n' %
                (key, error))
    assert res.get_data(as_text=True) == expected


@pytest.fixture()
def fail_queue(mocker):
    mocker.patch('rq.Queue.enqueue',
                 autospec=True)


def test_post_cost_report_missing_params(report_post_json_cost, api,
                                         fail_queue):
    payload = deepcopy(report_post_json_cost)
    payload['report_parameters']['costs'][0]['parameters'] = {}
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    errtext = res.get_data(as_text=True)
    assert errtext.startswith('{"errors":{"report_parameters":')
    assert 'Missing data for required field' in errtext


@pytest.mark.parametrize('type_,keys', [
    ('constant', ('cost', 'net', 'aggregation')),
    ('timeofday', ('cost', 'net', 'aggregation', 'times', 'fill')),
    ('datetime', ('cost', 'net', 'aggregation', 'datetimes', 'fill')),
])
def test_post_cost_report_missing_keys(
        type_, keys, api, make_cost_report, fail_queue):
    rep = make_cost_report(type_)
    for i in range(1, 4):
        for combo in itertools.combinations(keys, i):
            payload = deepcopy(rep)
            for k in combo:
                del payload['report_parameters']['costs'][0]['parameters'][k]
            res = api.post('/reports/', base_url=BASE_URL, json=payload)
            assert res.status_code == 400
            errtext = res.get_data(as_text=True)
            assert errtext.startswith('{"errors":{"report_parameters":')
            assert 'Missing data for required field' in errtext
            for k in combo:
                assert k in errtext


@pytest.mark.parametrize('type_', ('constant', 'timeofday', 'datetime',
                                   'errorband'))
@pytest.mark.parametrize('key,val', [
    ('cost', 'notfloat'),
    ('aggregation', 'min'),
    ('net', 'notbool'),
    ('cost', None),
    ('aggregation', None),
    ('net', None),
    ('extra', 'valid?')
])
def test_post_cost_report_params_invalid_common(
        make_cost_report, fail_queue, api, key, val, type_):
    payload = make_cost_report(type_)
    payload['report_parameters']['costs'][0]['parameters'][key] = val
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    errtext = res.get_data(as_text=True)
    assert errtext.startswith(
        '{"errors":{"report_parameters":[{"costs":{"0":{"parameters":{"%s"'
        % key)


def test_post_cost_report_params_invalid_type_for_params(
        make_cost_report, fail_queue, api):
    types = ('constant', 'timeofday', 'datetime',
             'errorband', 'not')
    for combo in itertools.permutations(types, 2):
        if combo[0] == 'not':
            continue
        payload = make_cost_report(combo[0])
        payload['report_parameters']['costs'][0]['type'] = combo[1]
        res = api.post('/reports/', base_url=BASE_URL, json=payload)
        assert res.status_code == 400
        errtext = res.get_data(as_text=True)
        assert errtext.startswith(
            '{"errors":{"report_parameters":[{"costs":{"0":{"parameters"')


@pytest.mark.parametrize('key,val', [
    ('fill', 'no'),
    ('fill', 0),
    ('fill', None),
    ('times', ['12:00', '06:33', 0]),
    ('times', ['12:00', '06:33', '06:61']),
    # too short
    ('cost', 1.0),
    ('cost', [1.0, 2.0]),
    ('cost', [1.0, 2.0, 3.0, 1.0]),
    ('times', ['00:00', '09:00']),
    ('times', ['00:00', '09:00', '10:00', '11:00']),
    ('timezone', 'notatz')
])
def test_post_cost_report_timeofday_invalid(
        make_cost_report, fail_queue, api, key, val):
    payload = make_cost_report('timeofday')
    payload['report_parameters']['costs'][0]['parameters'][key] = val
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    errtext = res.get_data(as_text=True)
    assert errtext.startswith(
        '{"errors":{"report_parameters":[{"costs":{"0":{"parameters":{')
    assert key in errtext


@pytest.mark.parametrize('key,val', [
    ('fill', 'no'),
    ('fill', 0),
    ('fill', None),
    ('datetimes', ['2020-01-01T00:00Z', 'nottime']),
    ('datetimes', ['2020-01-01T00:00Z', 0]),
    ('cost', 1.0),
    ('cost', [1.0, 2.0, 3.0]),
    ('datetimes', ['2020-01-01T00:00Z']),
    ('datetimes', ['2020-01-01T00:00Z', '2020-01-01T12:00Z',
                   '2020-01-02T00:00Z']),
    ('timezone', 'notatz')
])
def test_post_cost_report_datetime_invalid(
        make_cost_report, fail_queue, api, key, val):
    payload = make_cost_report('datetime')
    payload['report_parameters']['costs'][0]['parameters'][key] = val
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    errtext = res.get_data(as_text=True)
    assert errtext.startswith(
        '{"errors":{"report_parameters":[{"costs":{"0":{"parameters":{')
    assert key in errtext


def test_post_cost_report_errorband_no_bands(
        make_cost_report, fail_queue, api):
    payload = make_cost_report('errorband')
    payload['report_parameters']['costs'][0]['parameters']['bands'] = []
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    errtext = res.get_data(as_text=True)
    assert errtext.startswith(
        '{"errors":{"report_parameters":[{"costs":{"0":{"parameters":{"bands"')


def test_post_cost_report_errorband_recurs(
        make_cost_report, fail_queue, api):
    payload = make_cost_report('errorband')
    payload['report_parameters']['costs'][0]['parameters']['bands'][0][
        'cost_function'] = 'errorband'
    payload['report_parameters']['costs'][0]['parameters']['bands'][0][
        'cost_function_parameters'] = deepcopy(
            payload['report_parameters']['costs'][0]['parameters'])
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    errtext = res.get_data(as_text=True)
    assert errtext.startswith(
        '{"errors":{"report_parameters":[{"costs":{"0":'
        '{"parameters":{"bands":{"0"')


@pytest.mark.parametrize('range_', [
    [],
    (0,),
    (1, 'no'),
    (1, 1, 1),
    pytest.param(('-inf', 'inf'), marks=pytest.mark.xfail(strict=True)),
])
def test_post_cost_report_errorband_errorrange(
        make_cost_report, fail_queue, api, range_):
    payload = make_cost_report('errorband')
    payload['report_parameters']['costs'][0]['parameters']['bands'][0][
        'error_range'] = range_
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    errtext = res.get_data(as_text=True)
    assert errtext.startswith(
        '{"errors":{"report_parameters":[{"costs":{"0":'
        '{"parameters":{"bands":{"0":{"error_range"')


def test_post_cost_report_errorband_bad_cost_type(
        make_cost_report, fail_queue, api):
    payload = make_cost_report('errorband')
    types = ('constant', 'timeofday', 'datetime',
             'errorband', 'not')
    for combo in itertools.permutations(types, 2):
        if combo[0] == 'not':
            continue
        params = make_cost_report(combo[0])['report_parameters'][
            'costs'][0]['parameters']
        payload['report_parameters']['costs'][0]['parameters']['bands'] = [
            {
                'error_range': (0, 1),
                'cost_function': combo[1],
                'cost_function_parameters': params
            }
        ]
        res = api.post('/reports/', base_url=BASE_URL, json=payload)
        assert res.status_code == 400
        errtext = res.get_data(as_text=True)
        assert errtext.startswith(
            '{"errors":{"report_parameters":[{"costs":{"0":'
            '{"parameters":{"bands":{"0"')


def test_recompute(api, new_report):
    report_id = new_report()
    res = api.get(f'/reports/{report_id}/recompute', base_url=BASE_URL)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == report_id
    assert 'Location' in res.headers


def test_recompute_report_dne(api, missing_id):
    res = api.get(f'/reports/{missing_id}/recompute', base_url=BASE_URL)
    assert res.status_code == 404


def test_recompute_report_no_update(api, new_report, remove_all_perms):
    report_id = new_report()
    remove_all_perms('update', 'reports')
    res = api.get(f'/reports/{report_id}/recompute', base_url=BASE_URL)
    assert res.status_code == 404


def test_post_report_alt_url(api, report_post_json, mocked_queuing,
                             mocker, app):
    mocker.patch.dict(app.config, {'JOB_BASE_URL': 'http://0.0.0.1'})
    res = api.post('/reports/',
                   base_url=BASE_URL,
                   json=report_post_json)
    assert res.status_code == 201
    assert 'Location' in res.headers
    assert mocked_queuing.call_args[1]['base_url'] == 'http://0.0.0.1'


@pytest.mark.parametrize('fill', [
    '1.0', 0.1, 'inf', 'drop', 'forward', 9999.99,
    -1.9, 4, '99', '-82.8'
])
def test_post_report_forecast_fill(
        fill, api, report_post_json, mocked_queuing):
    payload = deepcopy(report_post_json)
    payload['report_parameters']['forecast_fill_method'] = fill
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 201
    assert 'Location' in res.headers


@pytest.mark.parametrize('missing_key', [
    'forecast',
    'reference_forecast',
    'observation',
])
def test_post_report_missing_object_pairs(
        api, report_post_json, missing_id, missing_key):
    payload = deepcopy(report_post_json)
    payload['report_parameters']['object_pairs'][0][missing_key] = missing_id
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    expected = ('{"errors":{"report_parameters":[{"object_pairs":%s}]}}\n' %
                ('{"0":{"'+missing_key+'":"Does not exist."}}'))
    assert res.get_data(as_text=True) == expected


@pytest.mark.parametrize('field,value', [
    ('variable', 'dni'),
    ('interval_length', 60),
    ('site_id', 'other_site'),
])
def test_post_report_observation_mismatch(
        api, mocker, report_post_json, field, value):
    pair = report_post_json['report_parameters']['object_pairs'][0]
    obsid = pair['observation']
    obs = deepcopy(demo_observations[obsid])
    obs[field] = value
    mocker.patch(
        'sfa_api.utils.storage_interface.read_observation',
        return_value=obs,
    )
    res = api.post('/reports/', base_url=BASE_URL, json=report_post_json)
    assert res.status_code == 400
    errors = res.json['errors']['report_parameters'][0]['object_pairs']['0']
    if field == 'interval_length':
        assert errors['observation'][field] == (
            f'Must be less than or equal to forecast {field}.')
    else:
        assert errors['observation'][field] == f'Must match forecast {field}.'


@pytest.mark.parametrize('field,value', [
    ('variable', 'dni'),
    ('interval_length', 120),
    ('aggregate_id', 'other_aggregate'),
])
def test_post_report_aggregate_mismatch(
        api, mocker, report_post_json, field, value):
    forecast_id = '39220780-76ae-4b11-bef1-7a75bdc784e3'
    aggregate_id = '458ffc27-df0b-11e9-b622-62adb5fd6af0'

    payload = deepcopy(report_post_json)
    payload['report_parameters']['object_pairs'][0].pop('observation')
    payload['report_parameters']['object_pairs'][0]['forecast'] = forecast_id
    payload['report_parameters']['object_pairs'][0]['aggregate'] = aggregate_id

    aggregate = deepcopy(demo_aggregates[aggregate_id])
    aggregate[field] = value
    mocker.patch(
        'sfa_api.utils.storage_interface.read_aggregate',
        return_value=aggregate,
    )
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    errors = res.json['errors']['report_parameters'][0]['object_pairs']['0']
    if field == 'interval_length':
        assert errors['aggregate'][field] == (
            f'Must be less than or equal to forecast {field}.')
    else:
        assert errors['aggregate'][field] == f'Must match forecast {field}.'


@pytest.mark.parametrize('field,value', [
    ('variable', 'dni'),
    ('interval_length', 120),
    ('site_id', 'other_site'),
    ('interval_label', 'ending'),
])
def test_post_report_reference_mismatch(
        api, mocker, report_post_json, field, value):
    pair = report_post_json['report_parameters']['object_pairs'][0]
    forecast_id = pair['forecast']
    forecast = demo_forecasts[forecast_id]
    reference_forecast = deepcopy(forecast)
    reference_forecast['forecast_id'] = "11c20780-76ae-4b11-bef1-7a75dde784c5"

    payload = deepcopy(report_post_json)
    pair = payload['report_parameters']['object_pairs'][0]
    pair['forecast'] = forecast_id
    pair['reference_forecast'] = reference_forecast['forecast_id']

    reference_forecast[field] = value
    mocker.patch(
        'sfa_api.utils.storage_interface.read_forecast',
        side_effect=[forecast, reference_forecast],
    )
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    errors = res.json['errors']['report_parameters'][0]['object_pairs']['0']
    assert errors['reference_forecast'][field] == (
        f'Must match forecast {field}.')


@pytest.mark.parametrize('field,value', [
    ('variable', 'dni'),
    ('interval_length', 120),
    ('site_id', 'other_site'),
    ('interval_label', 'ending'),
    ('axis', 'x'),
    ('constant_value', 50.0),
])
def test_post_report_reference_cdf_mismatch(
        api, mocker, report_post_json, field, value):
    parent_forecast_id = list(demo_group_cdf.keys())[0]
    parent_forecast = demo_group_cdf[parent_forecast_id]
    forecast_id = parent_forecast['constant_values'][0]['forecast_id']

    forecast = deepcopy(parent_forecast)
    forecast['forecast_id'] = forecast_id
    cvs = forecast.pop('constant_values')
    forecast['constant_value'] = cvs[0]['constant_value']
    forecast['parent'] = parent_forecast_id

    reference_forecast = deepcopy(forecast)
    reference_forecast['forecast_id'] = "11c20780-76ae-4b11-bef1-7a75dde784c5"
    reference_forecast['parent'] = "11c20780-76ae-4b11-bef1-2c75bbea84c5"

    payload = deepcopy(report_post_json)
    pair = payload['report_parameters']['object_pairs'][0]
    pair['forecast'] = forecast_id
    pair['reference_forecast'] = reference_forecast['forecast_id']
    pair['forecast_type'] = 'probabilistic_forecast_constant_value'

    reference_forecast[field] = value
    mocker.patch(
        'sfa_api.utils.storage_interface.read_cdf_forecast',
        side_effect=[forecast, reference_forecast],
    )
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    errors = res.json['errors']['report_parameters'][0]['object_pairs']['0']
    assert errors['reference_forecast'][field] == (
        f'Must match forecast {field}.')
