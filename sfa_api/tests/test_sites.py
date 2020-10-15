from itertools import combinations


import pytest


from sfa_api.conftest import VALID_SITE_JSON, BASE_URL, copy_update


def invalidate(json, key):
    new_json = json.copy()
    new_json[key] = 'invalid'
    return new_json


def removekey(json, key):
    new_json = json.copy()
    del new_json[key]
    return new_json


INVALID_NAME = copy_update(VALID_SITE_JSON, 'name', '<script>kiddies</script>')
INVALID_ELEVATION = invalidate(VALID_SITE_JSON, 'elevation')
INVALID_LATITUDE = invalidate(VALID_SITE_JSON, 'latitude')
INVALID_LONGITUDE = invalidate(VALID_SITE_JSON, 'longitude')
INVALID_TIMEZONE = invalidate(VALID_SITE_JSON, 'timezone')
INVALID_AC_CAPACITY = invalidate(VALID_SITE_JSON, 'ac_capacity')
INVALID_DC_CAPACITY = invalidate(VALID_SITE_JSON, 'dc_capacity')
INVALID_BACKTRACK = invalidate(VALID_SITE_JSON, 'backtrack')
INVALID_T_COEFF = invalidate(VALID_SITE_JSON, 'temperature_coefficient')
INVALID_COVERAGE = invalidate(VALID_SITE_JSON, 'ground_coverage_ratio')
INVALID_SURFACE_AZIMUTH = invalidate(VALID_SITE_JSON, 'surface_azimuth')
INVALID_SURFACE_TILT = invalidate(VALID_SITE_JSON, 'surface_tilt')
INVALID_TRACKING_TYPE = invalidate(VALID_SITE_JSON, 'tracking_type')

OUTSIDE_LATITUDE = VALID_SITE_JSON.copy()
OUTSIDE_LATITUDE['latitude'] = 91
OUTSIDE_LONGITUDE = VALID_SITE_JSON.copy()
OUTSIDE_LONGITUDE['longitude'] = 181


@pytest.mark.parametrize('payload', [
    VALID_SITE_JSON,
    removekey(VALID_SITE_JSON, 'extra_parameters'),
    removekey(VALID_SITE_JSON, 'modeling_parameters'),
    copy_update(VALID_SITE_JSON, 'modeling_parameters', {}),
    removekey(removekey(VALID_SITE_JSON, 'modeling_parameters'),
              'extra_parameters')
])
def test_site_post_201(api, payload):
    r = api.post('/sites/',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 201
    assert 'Location' in r.headers


VALID_MODELING_PARAMS = {
    "ac_capacity": 0.015,
    "dc_capacity": 0.015,
    "ac_loss_factor": 0,
    "dc_loss_factor": 0,
    "temperature_coefficient": -.2,
    "surface_azimuth": 180.0,
    "surface_tilt": 45.0,
    'axis_tilt': 0.0,
    'axis_azimuth': 180.0,
    'ground_coverage_ratio': 5.0,
    'backtrack': True,
    'max_rotation_angle': 70.0
}
COMMON_PARAMS = ['ac_capacity', 'dc_capacity', 'temperature_coefficient',
                 'ac_loss_factor', 'dc_loss_factor']
FIXED_PARAMS = ['surface_tilt', 'surface_azimuth']
SINGLEAXIS_PARAMS = ['axis_tilt', 'axis_azimuth', 'ground_coverage_ratio',
                     'backtrack', 'max_rotation_angle']


@pytest.mark.parametrize(
    'missing', (list(combinations(FIXED_PARAMS + COMMON_PARAMS, 1))
                + [['surface_tilt', 'surface_azimuth']]
                + [['surface_tilt', 'ac_capacity']]
                + [['ac_loss_factor', 'temperature_coefficient']])
    # a bit much to test all combinations
)
def test_site_post_missing_fixed_required_modeling_params(api, missing):
    payload = VALID_SITE_JSON.copy()
    modeling_params = {k: v for k, v in VALID_MODELING_PARAMS.items()
                       if k in (COMMON_PARAMS + FIXED_PARAMS)
                       and k not in missing}
    modeling_params['tracking_type'] = 'fixed'
    payload['modeling_parameters'] = modeling_params
    r = api.post('/sites/',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400
    for key in missing:
        assert key in r.json['errors']['modeling_parameters']


@pytest.mark.parametrize(
    'missing', (list(combinations(SINGLEAXIS_PARAMS + COMMON_PARAMS, 1))
                + [['axis_tilt', 'axis_azimuth']]
                + [['axis_tilt', 'ac_capacity']]
                + [['ac_loss_factor', 'temperature_coefficient']])
)
def test_site_post_missing_singleaxis_required_modeling_params(api, missing):
    payload = VALID_SITE_JSON.copy()
    modeling_params = {k: v for k, v in VALID_MODELING_PARAMS.items()
                       if k in (COMMON_PARAMS + SINGLEAXIS_PARAMS)
                       and k not in missing}
    modeling_params['tracking_type'] = 'single_axis'
    payload['modeling_parameters'] = modeling_params
    r = api.post('/sites/',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400
    for key in missing:
        assert key in r.json['errors']['modeling_parameters']


@pytest.mark.parametrize('tracking_type,params,extras', [
    (None, COMMON_PARAMS, COMMON_PARAMS),
    (None, COMMON_PARAMS + FIXED_PARAMS + SINGLEAXIS_PARAMS,
     COMMON_PARAMS + FIXED_PARAMS + SINGLEAXIS_PARAMS),
    ('fixed', COMMON_PARAMS + FIXED_PARAMS + SINGLEAXIS_PARAMS,
     SINGLEAXIS_PARAMS),
    ('fixed', COMMON_PARAMS + SINGLEAXIS_PARAMS,
     SINGLEAXIS_PARAMS + FIXED_PARAMS),
    ('single_axis', COMMON_PARAMS + FIXED_PARAMS + SINGLEAXIS_PARAMS,
     FIXED_PARAMS),
    ('single_axis', FIXED_PARAMS + SINGLEAXIS_PARAMS,
     FIXED_PARAMS + COMMON_PARAMS)
])
def test_site_post_extra_modeling_params(api, tracking_type, params, extras):
    """Make sure post fails with descriptive errors when extra parameters
    and/or missing parameters"""
    payload = VALID_SITE_JSON.copy()
    modeling_params = {k: v for k, v in VALID_MODELING_PARAMS.items()
                       if k in params}
    modeling_params['tracking_type'] = tracking_type
    payload['modeling_parameters'] = modeling_params
    r = api.post('/sites/',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400
    for key in extras:
        assert key in r.json['errors']['modeling_parameters']


@pytest.mark.parametrize('payload,message', [
    (INVALID_ELEVATION, '{"elevation":["Not a valid number."]}'),
    (INVALID_LATITUDE, '{"latitude":["Not a valid number."]}'),
    (OUTSIDE_LATITUDE, '{"latitude":["Must be greater than or equal to -90 and less than or equal to 90."]}'),  # NOQA
    (INVALID_LONGITUDE, '{"longitude":["Not a valid number."]}'),
    (OUTSIDE_LONGITUDE, '{"longitude":["Must be greater than or equal to -180 and less than or equal to 180."]}'),  # NOQA
    (INVALID_TIMEZONE, '{"timezone":["Invalid timezone."]}'),
    (INVALID_TRACKING_TYPE, '{"tracking_type":["Unknown field."]}'),
    (INVALID_NAME, '{"name":["Invalid characters in string."]}')
])
def test_site_post_400(api, payload, message):
    r = api.post('/sites/',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400
    assert r.get_data(as_text=True) == f'{{"errors":{message}}}\n'


def test_all_sites_get_200(api):
    r = api.get('/sites/',
                base_url=BASE_URL)
    assert r.status_code == 200
    resp = r.get_json()
    for r in resp:
        assert 'climate_zones' in r


@pytest.mark.parametrize('zone,hassome', [
    ('Reference Region 2', True),
    ('Reference Region 99', False),
    ('Reference+Region+3', True)
])
def test_all_sites_in_zone_get_200(api, zone, hassome):
    r = api.get(f'/sites/in/{zone}',
                base_url=BASE_URL)
    assert r.status_code == 200
    resp = r.get_json()
    if hassome:
        assert len(resp) > 0
        for r in resp:
            assert 'climate_zones' in r
    else:
        assert len(resp) == 0


@pytest.mark.parametrize('zone', [
    ''.join(['a'] * 256),
    ''
])
def test_all_sites_in_zone_get_404(api, zone):
    r = api.get(f'/sites/in/{zone}',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_site_get_200(api, site_id):
    r = api.get(f'/sites/{site_id}',
                base_url=BASE_URL)
    assert r.status_code == 200
    response = r.get_json()
    assert response['created_at'].endswith('+00:00')
    assert response['modified_at'].endswith('+00:00')
    assert 'climate_zones' in response


def test_site_get_404(api, missing_id):
    r = api.get(f'/sites/{missing_id}',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_site_observations_200(api, site_id):
    r = api.get(f'/sites/{site_id}/observations',
                base_url=BASE_URL)
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_site_observations_404(api, missing_id):
    r = api.get(f'/sites/{missing_id}/observations',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_site_forecasts_200(api, site_id_plant):
    r = api.get(f'/sites/{site_id_plant}/forecasts/single',
                base_url=BASE_URL)
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_site_forecasts_404(api, missing_id):
    r = api.get(f'/sites/{missing_id}/forecasts/single',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_site_delete_204(api, site_id):
    r = api.post('/sites/',
                 base_url=BASE_URL,
                 json=VALID_SITE_JSON)
    assert r.status_code == 201
    assert 'Location' in r.headers
    new_site_id = r.data.decode('utf-8')
    r = api.delete(f'/sites/{new_site_id}',
                   base_url=BASE_URL)
    assert r.status_code == 204


@pytest.mark.parametrize('up', [
    {'name': 'new name'},
    {},
    {'extra_parameters': 'here they are'},
    {'latitude': 0, 'modeling_parameters': {
        'tracking_type': 'fixed',
        'surface_azimuth': 180,
        'surface_tilt': 10,
        'ac_capacity': 0,
        'dc_capacity': 100,
        'ac_loss_factor': 0,
        'dc_loss_factor': 0,
        'temperature_coefficient': -0.001,
    }},
    {'elevation': 983, 'modeling_parameters': {
        'tracking_type': 'single_axis',
        'ground_coverage_ratio': 99,
        'backtrack': True,
        'axis_tilt': 10,
        'axis_azimuth': 173,
        'max_rotation_angle': 10,
        'ac_capacity': 0,
        'dc_capacity': 10,
        'ac_loss_factor': 9,
        'dc_loss_factor': 1,
        'temperature_coefficient': -0.001,
    }}
])
def test_site_update_success(api, site_id, up):
    res = api.post(f'/sites/{site_id}',
                   base_url=BASE_URL,
                   json=up)
    assert res.status_code == 200
    assert 'Location' in res.headers


@pytest.fixture(params=['missing', 'fx'])
def bad_id(missing_id, forecast_id, request):
    if request.param == 'missing':
        return missing_id
    else:
        return forecast_id


def test_site_update_404(api, bad_id):
    r = api.post(f'/sites/{bad_id}',
                 base_url=BASE_URL,
                 json={'name': 'new name'})
    assert r.status_code == 404


@pytest.mark.parametrize('payload,message', [
    ({'extra_parameters': 0}, '{"extra_parameters":["Not a valid string."]}'),
    ({'name': '#NOPE'}, '{"name":["Invalid characters in string."]}'),
    ({'backtrack': True}, '{"backtrack":["Unknown field."]}'),
    ({'modeling_parameters': {'tracking_type': 'single_axis', 'axis_tilt': 0}},
     '{"modeling_parameters":[{"ac_capacity":["Value required when tracking_type=\'single_axis\'"],"ac_loss_factor":["Value required when tracking_type=\'single_axis\'"],"axis_azimuth":["Value required when tracking_type=\'single_axis\'"],"backtrack":["Value required when tracking_type=\'single_axis\'"],"dc_capacity":["Value required when tracking_type=\'single_axis\'"],"dc_loss_factor":["Value required when tracking_type=\'single_axis\'"],"ground_coverage_ratio":["Value required when tracking_type=\'single_axis\'"],"max_rotation_angle":["Value required when tracking_type=\'single_axis\'"],"temperature_coefficient":["Value required when tracking_type=\'single_axis\'"]}]}'),  # NOQA
    ({'modeling_parameters': {'tracking_type': 'fixed', 'backtrack': True}},
     '{"modeling_parameters":[{"ac_capacity":["Value required when tracking_type=\'fixed\'"],"ac_loss_factor":["Value required when tracking_type=\'fixed\'"],"backtrack":["Field should be none with tracking_type=\'fixed\'"],"dc_capacity":["Value required when tracking_type=\'fixed\'"],"dc_loss_factor":["Value required when tracking_type=\'fixed\'"],"surface_azimuth":["Value required when tracking_type=\'fixed\'"],"surface_tilt":["Value required when tracking_type=\'fixed\'"],"temperature_coefficient":["Value required when tracking_type=\'fixed\'"]}]}'),  # NOQA
    ({'modeling_parameters': {'ac_capacity': 0}},
     '{"modeling_parameters":[{"ac_capacity":["Field must be null/none when tracking_type is none"]}]}')  # NOQA
])
def test_site_update_bad_request(api, site_id, payload, message):
    r = api.post(f'/sites/{site_id}',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400
    assert r.get_data(as_text=True) == f'{{"errors":{message}}}\n'
