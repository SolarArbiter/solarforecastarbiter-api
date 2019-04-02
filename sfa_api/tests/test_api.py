"""Tests that API maintains proper state after interactions
"""
import pandas.testing as pdt

from sfa_api.conftest import (VALID_SITE_JSON, VALID_OBS_JSON, VALID_FORECAST_JSON,
                              VALID_CDF_FORECAST_JSON)

def get_obs_list(api):
    get_obs = api.get('/observations/',
                      base_url='https://localhost')
    return get_obs.get_json()


def get_cdf_fx_list(api):
    get_cdf_fx = api.get('/forecasts/cdf/',
                         base_url='https://localhost')
    return get_cdf_fx.get_json()


def get_fx_list(api):
    get_fx = api.get('/forecasts/single/',
                     base_url='https://localhost')
    return get_fx.get_json()


def get_site_list(api):
    get_sites = api.get('/sites/',
                        base_url='https://localhost')
    return get_sites.get_json()


def get_site_fx(api, site_id):
    site_fx = api.get(f'/sites/{site_id}/forecasts/single',
                      base_url='https://localhost')
    return site_fx.get_json()


def get_site_cdf_fx(api, site_id):
    site_cdf_fx = api.get(f'/sites/{site_id}/forecasts/cdf',
                          base_url='https://localhost')
    return site_cdf_fx.get_json()


def get_site_obs(api, site_id):
    site_obs = api.get(f'/sites/{site_id}/observations',
                       base_url='https://localhost')
    return site_obs.get_json()


def test_create_delete_site(api):
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
    assert new_site in get_site_list(api)

    delete = api.delete(new_site_url)
    assert delete.status_code == 200
    assert new_site not in get_site_list(api)


def test_create_invalid_site(api):
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


def test_create_site_unauthenticated(api):
    # 401
    pass


def test_create_site_unauthorized(api):
    # 404
    pass

def test_create__delete_observation(api):
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
    assert new_obs in get_obs_list(api)
    assert new_obs in get_site_obs(api, new_obs['site_id'])

    delete = api.delete(new_obs_links_url)
    assert delete.status_code == 200
    assert new_obs not in get_obs_list(api)
    assert new_obs not in get_site_obs(api, new_obs['site_id'])



def test_create_observation_invalid(api):
    original_obs_list = get_obs_list(api)
    post = api.post('/observations/',
                    base_url='https://localhost',
                    json={'invalid': 'garbage'})
    assert post.status_code == 400
    assert original_obs_list == get_obs_list(api)



def test_create_observation_unauthorized(api):
    pass

def test_create_observation_unauthenticated(api):
    pass


def test_create_observation_site_dne(api, missing_id):
    observations = get_obs_list(api)
    obs_json = VALID_OBS_JSON.copy()
    obs_json.update({'site_id': missing_id})
    post = api.post('/observations/',
                    base_url='https://localhost',
                    json=obs_json)
    assert post.status_code == 404
    assert observations == get_obs_list(api)


def test_create_delete_forecast(api):
    post = api.post('/forecasts/single/',
                    base_url="https://localhost",
                    json=VALID_FORECAST_JSON)
    assert post.status_code == 201
    new_fx_id = post.data.decode('utf-8')
    new_fx_links_url = post.headers['Location']
    get_links = api.get(new_fx_links_url)
    assert get_links.status_code == 200
    new_fx_links = get_links.get_json()
    new_fx_url = new_fx_links['_links']['metadata']
    get_fx = api.get(new_fx_url)
    assert get_fx.status_code == 200
    new_fx = get_fx.get_json()
    assert new_fx['forecast_id'] == new_fx_id
    for key, value in VALID_FORECAST_JSON.items():
        assert new_fx[key] == value
    assert new_fx in get_fx_list(api)
    assert new_fx in get_site_fx(api, new_fx['site_id'])

    delete = api.delete(new_fx_links_url)
    assert delete.status_code == 200
    assert new_fx not in get_fx_list(api)
    assert new_fx not in get_site_fx(api, new_fx['site_id'])



def test_create_forecast_invalid(api):
    original_forecast_list = get_fx_list(api)
    post = api.post('/forecasts/single/',
                    base_url="https://localhost",
                    json={'invalid':'garbage'})
    assert post.status_code == 400
    assert original_forecast_list == get_fx_list(api)


def test_create_forecast_unauthorized(api):
    pass


def test_create_forecast_unauthenticated(api):
    pass


def test_post_forecast_site_dne(api, missing_id):
    forecasts = get_fx_list(api)
    fx_json = VALID_OBS_JSON.copy()
    fx_json.update({'site_id': missing_id})
    post = api.post('/forecasts/',
                    base_url='https://localhost',
                    json=fx_json)
    assert post.status_code == 404
    assert forecasts == get_fx_list(api)


def test_create_cdf_forecast(api):
    post = api.post('/forecasts/cdf/',
                    base_url="https://localhost",
                    json=VALID_CDF_FORECAST_JSON)
    assert post.status_code == 201
    new_cdf_fx_id = post.data.decode('utf-8')
    new_cdf_fx_url = post.headers['Location']
    get_cdf_fx = api.get(new_cdf_fx_url)
    assert get_cdf_fx.status_code == 200
    new_cdf_fx = get_cdf_fx.get_json()
    assert new_cdf_fx['forecast_id'] == new_cdf_fx_id
    for key, value in VALID_CDF_FORECAST_JSON.items():
        if key == 'constant_values':
            continue 
        else:
            assert new_cdf_fx[key] == value
    assert new_cdf_fx in get_cdf_fx_list(api)
    assert new_cdf_fx in get_site_cdf_fx(api, new_cdf_fx['site_id'])
    for value in new_cdf_fx['constant_values']:
        assert value['constant_value'] in VALID_CDF_FORECAST_JSON['constant_values']
        get_cdf_const = api.get(f'/forecasts/cdf/single/{value["forecast_id"]}',
                                base_url='https://localhost')
        assert get_cdf_const.status_code == 200


def test_create_cdf_forecast_invalid(api):
    pass


def test_create_cdf_forecast_unauthorized(api):
    pass


def test_create_cdf_forecast_site_dne(api):
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
