import pytest


from sfa_api.conftest import BASE_URL


def test_all_zones_get_200(api):
    r = api.get('/climatezones/',
                base_url=BASE_URL)
    assert r.status_code == 200
    resp = r.get_json()
    assert len(resp) == 9
    for r in resp:
        assert r['name'] in (f'Reference Region {i}'
                             for i in range(1, 10))
        assert 'created_at' in r
        assert 'modified_at' in r
        assert '_links' in r


@pytest.mark.parametrize('zone', [
    f'Reference Region {i}' for i in range(1, 10)] + [
        f'Reference+Region+{i}' for i in range(1, 10)]
)
def test_get_zone_200(api, zone):
    r = api.get(f'/climatezones/{zone}',
                base_url=BASE_URL)
    assert r.status_code == 200
    resp = r.get_json()
    assert resp['type'] == 'FeatureCollection'
    assert resp['features'][0]['properties']['Name'] == zone.replace('+', ' ')


@pytest.mark.parametrize('zone', [
    'Reference Region 10',
    ''.join(['b'] * 256)
])
def test_get_zone_404(api, zone):
    r = api.get(f'/climatezones/{zone}',
                base_url=BASE_URL)
    assert r.status_code == 404


@pytest.mark.parametrize('lat,lon,zones', [
    (32, -110.8, {'Reference Region 3'}),
    (20, -156.8, {'Reference Region 9'}),
    (37.8, -122.2, {'Reference Region 1'}),
    (0, 0, set())
])
def test_search_zone_200(api, lat, lon, zones):
    r = api.get(f'/climatezones/search?latitude={lat}&longitude={lon}',
                base_url=BASE_URL)
    assert r.status_code == 200
    resp = r.get_json()
    assert {r['name'] for r in resp} == zones


@pytest.mark.parametrize('qstr', [
    '?latitude=32',
    '?latitude=str',
    '?longitude=-110',
    '?latitude=32&longitude=str',
    '?latitude=91&longitude=-110',
    '?latitude=31&longitude=210'
])
def test_search_zone_400(api, qstr):
    r = api.get(f'/climatezones/search{qstr}',
                base_url=BASE_URL)
    assert r.status_code == 400
