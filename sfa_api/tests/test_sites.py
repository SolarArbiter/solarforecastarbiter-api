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
    "temperature_coefficient": -.002,
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
    (OUTSIDE_LATITUDE, '{"latitude":["Must be between -90 and 90."]}'),
    (INVALID_LONGITUDE, '{"longitude":["Not a valid number."]}'),
    (OUTSIDE_LONGITUDE, '{"longitude":["Must be between -180 and 180."]}'),
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


def test_site_get_200(api, site_id):
    r = api.get(f'/sites/{site_id}',
                base_url=BASE_URL)
    assert r.status_code == 200


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
