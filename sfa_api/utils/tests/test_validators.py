from copy import deepcopy
import datetime as dt


from marshmallow.exceptions import ValidationError
import pytest
import pytz


from sfa_api.conftest import (VALID_OBS_JSON, VALID_FORECAST_JSON,
                              VALID_CDF_FORECAST_JSON, VALID_FORECAST_AGG_JSON,
                              VALID_AGG_JSON)
from sfa_api.utils.errors import StorageAuthError
from sfa_api.utils import validators


@pytest.mark.parametrize('thetime', [
    '09:00', '9:00', '00:00'
])
def test_time_format(thetime):
    assert validators.TimeFormat('%H:%M')(thetime) == thetime


@pytest.mark.parametrize('bad', [
    '25:00', '00:00:00', 'ab:cd', '10:88'
])
def test_time_format_fail(bad):
    with pytest.raises(ValidationError):
        validators.TimeFormat('%H:%M')(bad)


@pytest.mark.parametrize('thestring', [
    'mysite', 'Site 1', 'A really long but otherwise OK site',
    "apostrophe '", 'site_99', 'site tucson, az',
    "Test (site)", 'w,', 'test-hyphen'
])
def test_userstring(thestring):
    assert validators.UserstringValidator()(
        thestring) == thestring


@pytest.mark.parametrize('thestring', [
    '<script>bac</script>', '<', ';delete',
    'site:a:b', 'site+1', 'site\\G',
    'site\n', '', ' ', "'", "'   ", '_', ',',
    ',_', '()', "'()',", "(){ :|:& };"
])
def test_invalid_userstring(thestring):
    with pytest.raises(ValidationError):
        validators.UserstringValidator()(thestring)


@pytest.mark.parametrize('tz', [
    'America/Phoenix',
    'Etc/GMT+7'
])
def test_timezonevalidator(tz):
    assert validators.TimezoneValidator()(tz) == tz


@pytest.mark.parametrize('tz', ['PDT', 'Germany/Berlin'])
def test_timezonevalidator_fail(tz):
    with pytest.raises(ValidationError):
        validators.TimezoneValidator()(tz)


@pytest.mark.parametrize('time_', [
    dt.datetime(2019, 1, 1, 12, 3, tzinfo=pytz.timezone('MST')),
    dt.datetime(2019, 1, 1, 12, 3),
    dt.datetime(1969, 12, 31, 17, 0, 1, tzinfo=pytz.timezone('MST')),
])
def test_timelimit_validator(time_):
    assert validators.TimeLimitValidator()(time_) == time_


@pytest.mark.parametrize('time_', [
    dt.datetime(2049, 1, 1, 12, 3),
    dt.datetime(1969, 12, 31, 14, 0, 1, tzinfo=pytz.timezone('MST')),
])
def test_timelimit_validator_fail(time_):
    with pytest.raises(ValidationError):
        validators.TimeLimitValidator()(time_)


@pytest.mark.parametrize("valid", [
    None, "observation_uncertainty", "0.0",
    ] + list(range(0, 101, 10))
)
def test_uncertainty_validator(valid):
    assert validators.UncertaintyValidator()(valid) == valid


@pytest.mark.parametrize("invalid", [
    "None", "bad string", "101", "-1.0"
])
def test_uncertainty_validator_errors(invalid):
    with pytest.raises(ValidationError):
        validators.UncertaintyValidator()(invalid)


@pytest.mark.parametrize("data", [
    {'variable': 'event', 'interval_label': 'event'},
    {'variable': 'notevent', 'interval_label': 'notevent'},
])
def test_validate_if_event(data):
    validators.validate_if_event({}, data)


@pytest.mark.parametrize("data", [
    {'variable': 'event', 'interval_label': 'notevent'},
    {'variable': 'notevent', 'interval_label': 'event'},
])
def test_validate_if_event_error(data):
    with pytest.raises(ValidationError):
        validators.validate_if_event({}, data)


# Create objects for testing report object pairs
VALID_CDF_SINGLE_JSON = deepcopy(VALID_CDF_FORECAST_JSON)
VALID_CDF_SINGLE_JSON.pop('constant_values')
VALID_CDF_SINGLE_JSON.update({
    'axis': 'x',
    'constant_value': '5.0'
})


VALID_FORECAST_AGG_JSON_60 = deepcopy(VALID_FORECAST_AGG_JSON)
VALID_FORECAST_AGG_JSON_60['interval_length'] = 60


VALID_AGG_JSON_WITH_ID = deepcopy(VALID_AGG_JSON)
VALID_AGG_JSON_WITH_ID.update({
    'aggregate_id': VALID_FORECAST_AGG_JSON_60['aggregate_id'],
})


VALID_EVENT_FORECAST_JSON = deepcopy(VALID_FORECAST_JSON)
VALID_EVENT_FORECAST_JSON.update({
    'variable': 'event',
    'interval_label': 'event',
})


VALID_EVENT_OBS_JSON = deepcopy(VALID_OBS_JSON)
VALID_EVENT_OBS_JSON.update({
    'variable': 'event',
    'interval_label': 'event',
})


@pytest.fixture()
def mock_reads(mocker):
    def fn(fx=None, obs=None, agg=None, ref_fx=None):
        storage_mock = mocker.MagicMock()
        storage_mock.read_forecast = mocker.MagicMock(side_effect=[fx, ref_fx])
        storage_mock.read_cdf_forecast_group = mocker.MagicMock(
            side_effect=[fx, ref_fx])
        storage_mock.read_cdf_forecast = mocker.MagicMock(
            side_effect=[fx, ref_fx])
        storage_mock.read_observation = mocker.MagicMock(return_value=obs)
        storage_mock.read_aggregate = mocker.MagicMock(return_value=agg)
        mocker.patch('sfa_api.utils.validators.get_storage',
                     return_value=storage_mock)
        return storage_mock
    return fn


@pytest.mark.parametrize('fx,meas', [
    (VALID_FORECAST_JSON, VALID_OBS_JSON),
    (VALID_CDF_FORECAST_JSON, VALID_OBS_JSON),
    (VALID_CDF_SINGLE_JSON, VALID_OBS_JSON),
    (VALID_FORECAST_AGG_JSON_60, VALID_AGG_JSON_WITH_ID),
    (VALID_EVENT_FORECAST_JSON, VALID_EVENT_OBS_JSON),
])
def test__ensure_forecast_measurement_compatibility(fx, meas):
    errors = validators._ensure_forecast_measurement_compatibility(fx, meas)
    assert not errors


@pytest.fixture(params=[
    ('variable', 'bad'), ('interval_length', 120), ('site_id', 'bad'),
    ('aggregate_id', 'bad')])
def update_object_params(request):
    def fn(obj):
        obj = deepcopy(obj)
        if request.param[0] not in obj:
            pytest.skip(f'{request.param[0]} not in object')
        obj[request.param[0]] = request.param[1]
        return obj, request.param[0]
    return fn


@pytest.mark.parametrize('fx,meas', [
    (VALID_FORECAST_JSON, VALID_OBS_JSON),
    (VALID_CDF_FORECAST_JSON, VALID_OBS_JSON),
    (VALID_CDF_SINGLE_JSON, VALID_OBS_JSON),
    (VALID_FORECAST_AGG_JSON_60, VALID_AGG_JSON_WITH_ID),
    (VALID_EVENT_FORECAST_JSON, VALID_EVENT_OBS_JSON),
])
def test__ensure_forecast_measurement_compatibility_errors(
        update_object_params, fx, meas):
    meas, error_key = update_object_params(meas)
    errors = validators._ensure_forecast_measurement_compatibility(fx, meas)
    if error_key == 'interval_length':
        assert errors[error_key] == ('Must be less than or equal to forecast '
                                     f'{error_key}.')
    else:
        assert errors[error_key] == f'Must match forecast {error_key}.'


@pytest.mark.parametrize('fx,obs,agg,forecast_type,include_ref_fx', [
    (VALID_FORECAST_JSON, VALID_OBS_JSON, None, 'forecast', False),
    (VALID_FORECAST_JSON, VALID_OBS_JSON, None, 'forecast', True),
    (VALID_FORECAST_AGG_JSON_60, None, VALID_AGG_JSON_WITH_ID,
     'forecast', False),
    (VALID_FORECAST_AGG_JSON_60, None, VALID_AGG_JSON_WITH_ID,
     'forecast', True),
    (VALID_CDF_FORECAST_JSON, VALID_OBS_JSON, None,
     'probabilistic_forecast', False),
    (VALID_CDF_FORECAST_JSON, VALID_OBS_JSON, None,
     'probabilistic_forecast', True),
    (VALID_CDF_SINGLE_JSON, VALID_OBS_JSON, None,
     'probabilistic_forecast_constant_value', False),
    (VALID_CDF_SINGLE_JSON, VALID_OBS_JSON, None,
     'probabilistic_forecast_constant_value', True),
    (VALID_EVENT_FORECAST_JSON, VALID_EVENT_OBS_JSON, None,
     'event_forecast', False),
    (VALID_EVENT_FORECAST_JSON, VALID_EVENT_OBS_JSON, None,
     'event_forecast', True),
])
def test_ensure_pair_compatibility(
        mock_reads, fx, obs, agg, forecast_type, include_ref_fx):
    if include_ref_fx:
        ref_fx = deepcopy(fx)
        ref_fx['name'] = 'test reference_forecast'
    else:
        ref_fx = None

    mock_reads(fx, obs, agg, ref_fx)

    pair = {
        'forecast': fx,
        'observation': obs,
        'aggregate': agg,
        'reference_forecast': ref_fx,
        'forecast_type': forecast_type,
    }
    errors = validators.ensure_pair_compatibility(pair)
    assert not errors


@pytest.fixture(params=[
    ('variable', 'bad'), ('interval_length', 120), ('site_id', 'bad'),
    ('aggregate_id', 'bad'), ('axis', 'y'), ('constant_value', 13.2)])
def update_reference_params(request):
    def fn(obj):
        obj = deepcopy(obj)
        if request.param[0] not in obj:
            pytest.skip(f'{request.param[0]} not in reference forecast')
        obj[request.param[0]] = request.param[1]
        return obj, request.param[0]
    return fn


@pytest.mark.parametrize('fx, forecast_type', [
    (VALID_FORECAST_JSON, 'forecast'),
    (VALID_FORECAST_AGG_JSON_60, 'forecast'),
    (VALID_CDF_FORECAST_JSON, 'probabilistic_forecast'),
    (VALID_CDF_SINGLE_JSON, 'probabilistic_forecast_constant_value'),
    (VALID_EVENT_FORECAST_JSON, 'event_forecast'),
])
def test__ensure_forecast_reference_compatibility_errors(
        update_reference_params, fx, forecast_type):
    ref_fx = deepcopy(fx)
    ref_fx['name'] = 'test reference_forecast'

    ref_fx, error_key = update_reference_params(ref_fx)

    errors = validators._ensure_forecast_reference_compatibility(
        fx, ref_fx, forecast_type)
    assert errors[error_key] == (
        f'Must match forecast {error_key}.')


@pytest.mark.parametrize('fx,obs,agg,forecast_type', [
    (VALID_FORECAST_JSON, VALID_OBS_JSON, None, 'forecast'),
    (VALID_FORECAST_AGG_JSON_60, None, VALID_AGG_JSON_WITH_ID, 'forecast'),
    (VALID_CDF_FORECAST_JSON, VALID_OBS_JSON, None, 'probabilistic_forecast'),
    (VALID_CDF_SINGLE_JSON, VALID_OBS_JSON, None,
     'probabilistic_forecast_constant_value'),
    (VALID_EVENT_FORECAST_JSON, VALID_EVENT_OBS_JSON, None, 'event_forecast'),
])
def test_ensure_pair_compatibility_reference_errors(
        update_reference_params, mock_reads, fx, obs, agg, forecast_type):
    ref_fx = deepcopy(fx)
    ref_fx['name'] = 'test reference_forecast'

    ref_fx, error_key = update_reference_params(ref_fx)

    mock_reads(fx, obs, agg, ref_fx)

    pair = {
        'forecast': fx,
        'observation': obs,
        'aggregate': agg,
        'reference_forecast': ref_fx,
        'forecast_type': forecast_type,
    }

    with pytest.raises(ValidationError) as e:
        validators.ensure_pair_compatibility(pair)
    errors = e.value.messages
    assert errors['reference_forecast'][error_key] == (
        f'Must match forecast {error_key}.')
    assert 'observation' not in errors
    assert 'aggregate' not in errors


@pytest.mark.parametrize('fx,obs,agg,forecast_type,include_ref_fx', [
    (VALID_FORECAST_JSON, VALID_OBS_JSON, None, 'forecast', False),
    (VALID_FORECAST_JSON, VALID_OBS_JSON, None, 'forecast', True),
    (VALID_FORECAST_AGG_JSON_60, None, VALID_AGG_JSON_WITH_ID,
     'forecast', False),
    (VALID_FORECAST_AGG_JSON_60, None, VALID_AGG_JSON_WITH_ID,
     'forecast', True),
    (VALID_CDF_FORECAST_JSON, VALID_OBS_JSON, None,
     'probabilistic_forecast', False),
    (VALID_CDF_FORECAST_JSON, VALID_OBS_JSON, None,
     'probabilistic_forecast', True),
    (VALID_CDF_SINGLE_JSON, VALID_OBS_JSON, None,
     'probabilistic_forecast_constant_value', False),
    (VALID_CDF_SINGLE_JSON, VALID_OBS_JSON, None,
     'probabilistic_forecast_constant_value', True),
    (VALID_EVENT_FORECAST_JSON, VALID_EVENT_OBS_JSON, None,
     'event_forecast', False),
    (VALID_EVENT_FORECAST_JSON, VALID_EVENT_OBS_JSON, None,
     'event_forecast', True),
])
def test_ensure_pair_compatibility_agg_obs_errors(
        update_object_params, mock_reads, fx, obs, agg, forecast_type,
        include_ref_fx):
    if include_ref_fx:
        ref_fx = deepcopy(fx)
        ref_fx['name'] = 'test reference_forecast'
    else:
        ref_fx = None

    if obs is not None:
        error_field = 'observation'
        dne_field = 'aggregate'
        obs, error_key = update_object_params(obs)
    elif agg is not None:
        error_field = 'aggregate'
        dne_field = 'observation'
        agg, error_key = update_object_params(agg)
    mock_reads(fx, obs, agg, ref_fx)

    pair = {
        'forecast': fx,
        'observation': obs,
        'aggregate': agg,
        'reference_forecast': ref_fx,
        'forecast_type': forecast_type,
    }

    with pytest.raises(ValidationError) as e:
        validators.ensure_pair_compatibility(pair)
    errors = e.value.messages
    field_errors = errors[error_field]
    if error_key == 'interval_length':
        assert field_errors[error_key] == (
            f'Must be less than or equal to forecast {error_key}.')
    else:
        assert field_errors[error_key] == f'Must match forecast {error_key}.'
    assert dne_field not in errors
    assert 'reference_forecast' not in errors


@pytest.fixture()
def mock_reads_with_failure(mocker):
    def fn(failure, fx=None, obs=None, agg=None, ref_fx=None):
        storage_mock = mocker.MagicMock()
        if failure == 'forecast':
            forecast_se = [StorageAuthError, ref_fx]
        elif failure == 'reference_forecast':
            forecast_se = [fx, StorageAuthError]
        else:
            forecast_se = [fx, ref_fx]
        storage_mock.read_forecast = mocker.MagicMock(
            side_effect=forecast_se)
        storage_mock.read_cdf_forecast_group = mocker.MagicMock(
            side_effect=forecast_se)
        storage_mock.read_cdf_forecast = mocker.MagicMock(
            side_effect=forecast_se)
        if failure == 'observation':
            storage_mock.read_observation = mocker.MagicMock(
                side_effect=StorageAuthError)
        else:
            storage_mock.read_observation = mocker.MagicMock(return_value=obs)
        if failure == 'aggregate':
            storage_mock.read_aggregate = mocker.MagicMock(
                side_effect=StorageAuthError)
        else:
            storage_mock.read_aggregate = mocker.MagicMock(return_value=agg)
        mocker.patch('sfa_api.utils.validators.get_storage',
                     return_value=storage_mock)
        return storage_mock
    return fn


@pytest.mark.parametrize('fx,obs,agg,failure_mode', [
    (VALID_FORECAST_JSON, VALID_OBS_JSON, None, 'forecast'),
    (VALID_FORECAST_JSON, VALID_OBS_JSON, None, 'observation'),
    (VALID_FORECAST_JSON, VALID_OBS_JSON, None, 'reference_forecast'),
    (VALID_FORECAST_AGG_JSON_60, None, VALID_AGG_JSON_WITH_ID, 'forecast'),
    (VALID_FORECAST_AGG_JSON_60, None, VALID_AGG_JSON_WITH_ID, 'aggregate'),
    (VALID_FORECAST_AGG_JSON_60, None, VALID_AGG_JSON_WITH_ID,
     'reference_forecast'),
])
def test_ensure_pair_compatibility_object_dne(
        mock_reads_with_failure, fx, obs, agg, failure_mode):
    ref_fx = deepcopy(fx)
    ref_fx['name'] = 'test reference_forecast'

    mock_reads_with_failure(failure_mode, fx, obs, agg, ref_fx)

    pair = {
        'forecast': fx,
        'observation': obs,
        'aggregate': agg,
        'reference_forecast': ref_fx,
        'forecast_type': 'forecast',
    }

    with pytest.raises(ValidationError) as e:
        validators.ensure_pair_compatibility(pair)
    errors = e.value.messages
    assert errors[failure_mode] == 'Does not exist.'
