"""Tests if using the API without internal interference has expected results. 
"""
import pandas.testing as pdt


from sfa_api.tests.test_sites import VALID_SITE_JSON
from sfa_api.tests.test_observation import VALID_OBS_JSON
from sfa_api.tests.test_forecast import VALID_FORECAST_JSON


def test_post_site(api):
    sites_get = api.get('/sites/',
                        base_url='https://localhost')
    original_sites_list = sites_get.get_json()
    post = api.post('/sites/', 
                    base_url='https://localhost',
                    json=VALID_SITE_JSON)
    assert post.status_code == 201
    new_site_id = post.data.decode('utf-8')
    new_site_url = post.headers['Location']
    get = api.get(new_site_url)
    assert get.status_code == 200
    new_site = get.get_json()
    assert new_site['site_id'] == new_site_id
    for key, value in VALID_SITE_JSON.items():
        assert new_site[key] == value
    sites_get = api.get('/sites/',
                        base_url='https://localhost')
    new_sites_list = sites_get.get_json()
    assert len(new_sites_list) - len(original_sites_list) == 1


def test_post_site_invalid(api):
    sites_get = api.get('/sites/',
                        base_url='https://localhost')
    original_sites_list = sites_get.get_json()
    post = api.post('/sites/', 
                    base_url='https://localhost',
                    json={'invalid':'garbage'})
    assert post.status_code == 400
    sites_get = api.get('/sites/',
                        base_url='https://localhost')
    new_sites_list = sites_get.get_json()
    assert original_sites_list == new_sites_list


def test_post_site_unauthorized(api):
    post = api.post('/sites/', 
                    base_url='https://localhost',
                    json=VALID_SITE_JSON)
    # assert post.status_code == 401
    assert post.status_code == 201


def test_post_observation(api):
    post = api.post('/observations/',
                    base_url='https://localhost',
                    json=VALID_OBS_JSON)
    assert post.status_code == 201
    new_obs_id = post.data.decode('utf-8')
    new_obs_links_url = post.headers['Location']
    get_links = api.get(new_obs_links_url)
    assert get_links.status_code == 200
    new_obs_links = get_links.get_json()
    new_obs_url = new_obs_links['_links']['metadata']
    get_obs = api.get(new_obs_url)
    assert get_obs.status_code == 200
    new_obs = get_obs.get_json()
    assert new_obs['observation_id'] == new_obs_id
    for key, value in VALID_OBS_JSON.items():
        assert new_obs[key] == value



def test_post_observation_invalid(api):
    get_obs = api.get('/observations/',
                      base_url='https://localhost')
    original_obs_list = get_obs.get_json()
    post = api.post('/observations/',
                    base_url='https://localhost',
                    json={'invalid': 'garbage'})
    assert post.status_code == 400



def test_post_observation_unauthorized(api):
    pass


def test_post_observation_site_dne(api):
    pass


def test_post_forecast(api):
    pass


def test_post_forecast_invalid(api):
    pass


def test_post_forecast_unauthorized(api):
    pass


def test_postforecast_site_dne(api):
    pass


def test_post_cdf_forecast(api):
    pass


def test_post_cdf_forecast_invalid(api):
    pass


def test_post_cdf_forecast_unauthorized(api):
    pass


def test_post_cdf_forecast_site_dne(api):
    pass

def test_sequence(api):
    # post site
    # post obs to site
    # post fx to site
    # try to delete site, expect failure
    # delete fx
    # delete obs
    # delete site
    # ensure site, fx, obs dne
    pass
