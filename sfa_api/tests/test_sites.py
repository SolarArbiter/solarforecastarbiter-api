import pytest

from sfa_api.conftest import VALID_SITE_JSON


def invalidate(json, key):
    new_json = json.copy()
    new_json[key] = 'invalid'
    return new_json


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
    (VALID_SITE_JSON)
])
def test_site_post_201(api, payload):
    r = api.post('/sites/',
                 base_url='https://localhost',
                 json=payload)
    assert r.status_code == 201
    assert 'Location' in r.headers


@pytest.mark.parametrize('payload,message', [
    (INVALID_ELEVATION, '{"elevation":["Not a valid number."]}'),
    (INVALID_LATITUDE, '{"latitude":["Not a valid number."]}'),
    (OUTSIDE_LATITUDE, '{"latitude":["Must be between -90 and 90."]}'),
    (INVALID_LONGITUDE, '{"longitude":["Not a valid number."]}'),
    (OUTSIDE_LONGITUDE, '{"longitude":["Must be between -180 and 180."]}'),
    (INVALID_TIMEZONE, '{"timezone":["Invalid timezone."]}'),
])
def test_site_post_400(api, payload, message):
    r = api.post('/sites/',
                 base_url='https://localhost',
                 json=payload)
    assert r.status_code == 400
    assert r.get_data(as_text=True) == f'{{"errors":{message}}}\n'


def test_all_sites_get_200(api):
    r = api.get('/sites/',
                base_url='https://localhost')
    assert r.status_code == 200


def test_site_get_200(api, site_id):
    r = api.get(f'/sites/{site_id}',
                base_url='https://localhost')
    assert r.status_code == 200


def test_site_get_404(api, missing_id):
    r = api.get(f'/sites/{missing_id}',
                base_url='https://localhost')
    assert r.status_code == 404


def test_site_observations_200(api, site_id):
    r = api.get(f'/sites/{site_id}/observations',
                base_url='https://localhost')
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_site_observations_404(api, missing_id):
    r = api.get(f'/sites/{missing_id}/observations',
                base_url='https://localhost')
    assert r.status_code == 404


def test_site_forecasts_200(api, site_id_plant):
    r = api.get(f'/sites/{site_id_plant}/forecasts/single',
                base_url='https://localhost')
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_site_forecasts_404(api, missing_id):
    r = api.get(f'/sites/{missing_id}/forecasts/single',
                base_url='https://localhost')
    assert r.status_code == 404


def test_site_delete_200(api, site_id):
    r = api.delete(f'/sites/{site_id}',
                   base_url='https://localhost')
    assert r.status_code == 200


def test_site_delete_404(api, missing_id):
    r = api.delete(f'/sites/{missing_id}',
                   base_url='https://localhost')
    assert r.status_code == 404
