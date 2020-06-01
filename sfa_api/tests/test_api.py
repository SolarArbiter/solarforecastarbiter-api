"""Tests that API maintains proper state after interactions
"""
import pytest
import re
import uuid


from sfa_api.conftest import (VALID_SITE_JSON, VALID_OBS_JSON,
                              VALID_FORECAST_JSON, VALID_CDF_FORECAST_JSON,
                              BASE_URL)


invalid_json = {'invalid': 'garbage'}


@pytest.fixture()
def auth_header(auth_token):
    return {'Authorization': f'Bearer {auth_token}'}


def get_obs_list(sql_api, auth_header):
    get_obs = sql_api.get('/observations/',
                          base_url=BASE_URL,
                          headers=auth_header)
    return get_obs.get_json()


def get_cdf_fx_list(sql_api, auth_header):
    get_cdf_fx = sql_api.get('/forecasts/cdf/',
                             headers=auth_header,
                             base_url=BASE_URL)
    return get_cdf_fx.get_json()


def get_fx_list(sql_api, auth_header):
    get_fx = sql_api.get('/forecasts/single/',
                         headers=auth_header,
                         base_url=BASE_URL)
    return get_fx.get_json()


def get_site_list(sql_api, auth_header):
    get_sites = sql_api.get('/sites/',
                            headers=auth_header,
                            base_url=BASE_URL)
    return get_sites.get_json()


def get_site_fx(sql_api, auth_header, site_id):
    site_fx = sql_api.get(f'/sites/{site_id}/forecasts/single',
                          headers=auth_header,
                          base_url=BASE_URL)
    return site_fx.get_json()


def get_site_cdf_fx(sql_api, auth_header, site_id):
    site_cdf_fx = sql_api.get(f'/sites/{site_id}/forecasts/cdf',
                              headers=auth_header,
                              base_url=BASE_URL)
    return site_cdf_fx.get_json()


def get_site_obs(sql_api, auth_header, site_id):
    site_obs = sql_api.get(f'/sites/{site_id}/observations',
                           headers=auth_header,
                           base_url=BASE_URL)
    return site_obs.get_json()


def test_create_delete_site(sql_api, auth_header):
    post = sql_api.post('/sites/',
                        base_url=BASE_URL,
                        headers=auth_header,
                        json=VALID_SITE_JSON)
    assert post.status_code == 201
    new_site_id = post.data.decode('utf-8')
    new_site_url = post.headers['Location']
    get = sql_api.get(new_site_url, headers=auth_header)
    assert get.status_code == 200
    new_site = get.get_json()
    assert new_site['site_id'] == new_site_id
    for key, value in VALID_SITE_JSON.items():
        if key == 'modeling_parameters':
            for k, v in VALID_SITE_JSON['modeling_parameters'].items():
                assert new_site['modeling_parameters'][k] == v
        else:
            assert new_site[key] == value
    assert new_site in get_site_list(sql_api, auth_header)

    delete = sql_api.delete(new_site_url, headers=auth_header)
    assert delete.status_code == 204
    assert new_site not in get_site_list(sql_api, auth_header)


def test_create_invalid_site(sql_api, auth_header):
    original_sites_list = get_site_list(sql_api, auth_header)
    post = sql_api.post('/sites/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=invalid_json)
    assert post.status_code == 400
    assert original_sites_list == get_site_list(sql_api, auth_header)


def test_create_site_unauthenticated(sql_api):
    post = sql_api.post('/sites/',
                        base_url=BASE_URL,
                        json=VALID_SITE_JSON)
    assert post.status_code == 401


def test_create_site_unauthorized(sql_api, auth_header):
    # 404
    pass


def test_create_delete_observation(sql_api, auth_header, mocked_queuing,
                                   obs_vals, startend):
    post = sql_api.post('/observations/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=VALID_OBS_JSON)
    assert post.status_code == 201
    new_obs_id = post.data.decode('utf-8')
    new_obs_links_url = post.headers['Location']
    get_links = sql_api.get(new_obs_links_url, headers=auth_header)
    assert get_links.status_code == 200
    new_obs_links = get_links.get_json()
    new_obs_url = new_obs_links['_links']['metadata']
    get_obs = sql_api.get(new_obs_url, headers=auth_header)
    assert get_obs.status_code == 200
    new_obs = get_obs.get_json()
    assert new_obs['observation_id'] == new_obs_id
    for key, value in VALID_OBS_JSON.items():
        assert new_obs[key] == value
    assert new_obs in get_obs_list(sql_api, auth_header)
    assert new_obs in get_site_obs(sql_api, auth_header, new_obs['site_id'])

    # Post json values to the observation
    obs_vals['quality_flag'] = 0
    obs_vals['timestamp'] = obs_vals.index
    json_values = obs_vals.to_dict(orient='records')

    post_values = sql_api.post(f'/observations/{new_obs_id}/values',
                               headers=auth_header,
                               base_url=BASE_URL,
                               json={'values': json_values})
    assert post_values.status_code == 201
    get_values = sql_api.get(f'/observations/{new_obs_id}/values{startend}',
                             base_url=BASE_URL,
                             headers={'Accept': 'application/json',
                                      **auth_header})
    assert get_values.status_code == 200

    # post csv_values to the observation
    obs_vals['quality_flag'] = 0
    csv_values = obs_vals.to_csv()
    post_values = sql_api.post(f'/observations/{new_obs_id}/values',
                               base_url=BASE_URL,
                               headers={'Content-Type': 'text/csv',
                                        **auth_header},
                               data=csv_values)
    assert post_values.status_code == 201
    get_values = sql_api.get(f'/observations/{new_obs_id}/values{startend}',
                             base_url=BASE_URL,
                             headers={'Accept': 'text/csv', **auth_header})
    assert get_values.status_code == 200

    delete = sql_api.delete(new_obs_links_url, headers=auth_header)
    assert delete.status_code == 204
    assert new_obs not in get_obs_list(sql_api, auth_header)
    assert new_obs not in get_site_obs(sql_api, auth_header,
                                       new_obs['site_id'])
    get_values = sql_api.get(f'/observations/{new_obs_id}/values{startend}',
                             base_url=BASE_URL,
                             headers={'Accept': 'text/csv', **auth_header})
    assert get_values.status_code == 404


def test_create_observation_invalid(sql_api, auth_header):
    original_obs_list = get_obs_list(sql_api, auth_header)
    post = sql_api.post('/observations/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json={'invalid': 'garbage'})
    assert post.status_code == 400
    assert original_obs_list == get_obs_list(sql_api, auth_header)


def test_create_observation_unauthorized(sql_api, auth_header):
    pass


def test_create_observation_site_dne(sql_api, auth_header, missing_id):
    observations = get_obs_list(sql_api, auth_header)
    obs_json = VALID_OBS_JSON.copy()
    obs_json.update({'site_id': missing_id})
    post = sql_api.post('/observations/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=obs_json)
    assert post.status_code == 404
    assert observations == get_obs_list(sql_api, auth_header)


def test_create_delete_forecast(sql_api, auth_header, fx_vals, startend):
    post = sql_api.post('/forecasts/single/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=VALID_FORECAST_JSON)
    assert post.status_code == 201
    new_fx_id = post.data.decode('utf-8')
    new_fx_links_url = post.headers['Location']
    get_links = sql_api.get(new_fx_links_url, headers=auth_header)
    assert get_links.status_code == 200
    new_fx_links = get_links.get_json()
    new_fx_url = new_fx_links['_links']['metadata']
    get_fx = sql_api.get(new_fx_url, headers=auth_header)
    assert get_fx.status_code == 200
    new_fx = get_fx.get_json()
    assert new_fx['forecast_id'] == new_fx_id
    for key, value in VALID_FORECAST_JSON.items():
        assert new_fx[key] == value
    assert new_fx in get_fx_list(sql_api, auth_header)
    assert new_fx in get_site_fx(sql_api, auth_header, new_fx['site_id'])

    # Post json values to the forecast
    fx_vals['timestamp'] = fx_vals.index
    json_values = fx_vals.to_dict(orient='records')

    post_values = sql_api.post(
        f'/forecasts/single/{new_fx_id}/values',
        headers=auth_header,
        base_url=BASE_URL,
        json={'values': json_values})
    assert post_values.status_code == 201

    # request json values
    get_values = sql_api.get(f'/forecasts/single/{new_fx_id}/values{startend}',
                             base_url=BASE_URL,
                             headers={'Accept': 'application/json',
                                      **auth_header})
    assert get_values.status_code == 200

    # post csv_values to the forecasts
    csv_values = fx_vals.to_csv()

    post_values = sql_api.post(f'/forecasts/single/{new_fx_id}/values',
                               base_url=BASE_URL,
                               headers={'Content-Type': 'text/csv',
                                        **auth_header},
                               data=csv_values)
    assert post_values.status_code == 201

    # request csv values
    get_values = sql_api.get(f'/forecasts/single/{new_fx_id}/values{startend}',
                             base_url=BASE_URL,
                             headers={'Accept': 'text/csv', **auth_header})
    assert get_values.status_code == 200

    delete = sql_api.delete(new_fx_links_url, headers=auth_header)
    assert delete.status_code == 204
    assert new_fx not in get_fx_list(sql_api, auth_header)
    assert new_fx not in get_site_fx(sql_api, auth_header,
                                     new_fx['site_id'])

    get_values = sql_api.get(
        f'/forecasts/single/{new_fx_id}/values{startend}',
        base_url=BASE_URL,
        headers={'Accept': 'text/csv', **auth_header})
    assert get_values.status_code == 404


def test_create_forecast_invalid(sql_api, auth_header):
    original_forecast_list = get_fx_list(sql_api, auth_header)
    post = sql_api.post('/forecasts/single/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=invalid_json)
    assert post.status_code == 400
    assert original_forecast_list == get_fx_list(sql_api, auth_header)


def test_create_forecast_unauthorized(sql_api, auth_header):
    pass


def test_post_forecast_site_dne(sql_api, auth_header, missing_id):
    forecasts = get_fx_list(sql_api, auth_header)
    fx_json = VALID_FORECAST_JSON.copy()
    fx_json.update({'site_id': missing_id})
    post = sql_api.post('/forecasts/single/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=fx_json)
    assert post.status_code == 404
    assert forecasts == get_fx_list(sql_api, auth_header)


def test_create_delete_cdf_forecast(sql_api, auth_header, fx_vals, startend):
    post = sql_api.post('/forecasts/cdf/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=VALID_CDF_FORECAST_JSON)
    assert post.status_code == 201
    new_cdf_fx_id = post.data.decode('utf-8')
    new_cdf_fx_url = post.headers['Location']
    get_cdf_fx = sql_api.get(new_cdf_fx_url, headers=auth_header)
    assert get_cdf_fx.status_code == 200
    new_cdf_fx = get_cdf_fx.get_json()
    assert new_cdf_fx['forecast_id'] == new_cdf_fx_id
    for key, value in VALID_CDF_FORECAST_JSON.items():
        if key == 'constant_values':
            continue
        else:
            assert new_cdf_fx[key] == value
    assert new_cdf_fx in get_cdf_fx_list(sql_api, auth_header)
    assert new_cdf_fx in get_site_cdf_fx(sql_api, auth_header,
                                         new_cdf_fx['site_id'])
    for value in new_cdf_fx['constant_values']:
        static_vals = VALID_CDF_FORECAST_JSON['constant_values']
        assert value['constant_value'] in static_vals
        get_const = sql_api.get(
            f'/forecasts/cdf/single/{value["forecast_id"]}',
            headers=auth_header,
            base_url=BASE_URL)
        assert get_const.status_code == 200
        get_cdf_const_values = sql_api.get(
            value['_links']['values'] + startend,
            headers=auth_header)
        assert get_cdf_const_values.status_code == 200

        # Post values to the forecast
        fx_vals['timestamp'] = fx_vals.index
        json_values = fx_vals.to_dict(orient='records')

        post_values = sql_api.post(value['_links']['values'] + startend,
                                   headers=auth_header,
                                   json={'values': json_values})
        assert post_values.status_code == 201
        get_values = sql_api.get(value['_links']['values'] + startend,
                                 headers={'Accept': 'application/json',
                                          **auth_header})
        assert get_values.status_code == 200

    delete = sql_api.delete(new_cdf_fx_url, headers=auth_header)
    assert delete.status_code == 204
    assert new_cdf_fx not in get_cdf_fx_list(sql_api, auth_header)
    assert new_cdf_fx not in get_site_cdf_fx(sql_api, auth_header,
                                             new_cdf_fx['site_id'])
    for value in new_cdf_fx['constant_values']:
        fx_id = value['forecast_id']
        get = sql_api.get(f'/forecasts/cdf/single/{fx_id}',
                          headers=auth_header,
                          base_url=BASE_URL)
        assert get.status_code == 404


def test_create_cdf_forecast_invalid(sql_api, auth_header):
    original_cdf_fx_list = get_cdf_fx_list(sql_api, auth_header)
    post = sql_api.post('/forecasts/cdf/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json={'invalid': 'garbage'})
    assert post.status_code == 400
    assert original_cdf_fx_list == get_cdf_fx_list(sql_api, auth_header)


def test_create_cdf_forecast_unauthenticated(sql_api):
    post = sql_api.post('/forecasts/cdf/',
                        base_url=BASE_URL,
                        json=VALID_CDF_FORECAST_JSON)
    assert post.status_code == 401


def test_create_cdf_forecast_unauthorized(sql_api, auth_header):
    pass


def test_create_cdf_forecast_site_dne(sql_api, auth_header, missing_id):
    cdf_fx_list = get_cdf_fx_list(sql_api, auth_header)
    fx_json = VALID_CDF_FORECAST_JSON.copy()
    fx_json.update({'site_id': missing_id})
    post = sql_api.post('/forecasts/cdf/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=fx_json)
    assert post.status_code == 404
    assert cdf_fx_list == get_cdf_fx_list(sql_api, auth_header)


def test_sequence(sql_api, auth_header):
    # Create a site
    post = sql_api.post('/sites/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=VALID_SITE_JSON)
    assert post.status_code == 201
    new_site_id = post.data.decode('utf-8')
    new_site_url = post.headers['Location']
    get = sql_api.get(new_site_url, headers=auth_header)
    assert get.status_code == 200
    new_site = get.get_json()

    # Create obs at site
    obs_json = VALID_OBS_JSON.copy()
    obs_json['site_id'] = new_site_id
    post = sql_api.post('/observations/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=obs_json)
    assert post.status_code == 201
    new_obs_id = post.data.decode('utf-8')
    new_obs_links_url = post.headers['Location']
    get_links = sql_api.get(new_obs_links_url, headers=auth_header)
    assert get_links.status_code == 200
    new_obs_links = get_links.get_json()
    new_obs_url = new_obs_links['_links']['metadata']
    get_obs = sql_api.get(new_obs_url, headers=auth_header)
    assert get_obs.status_code == 200
    new_obs = get_obs.get_json()

    # Create FX at site
    fx_json = VALID_FORECAST_JSON.copy()
    fx_json['site_id'] = new_site_id
    post = sql_api.post('/forecasts/single/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=VALID_FORECAST_JSON)
    assert post.status_code == 201
    new_fx_id = post.data.decode('utf-8')
    new_fx_links_url = post.headers['Location']
    get_links = sql_api.get(new_fx_links_url, headers=auth_header)
    assert get_links.status_code == 200
    new_fx_links = get_links.get_json()
    new_fx_url = new_fx_links['_links']['metadata']
    get_fx = sql_api.get(new_fx_url, headers=auth_header)
    assert get_fx.status_code == 200
    new_fx = get_fx.get_json()

    # Create a cdf fx at the site
    post = sql_api.post('/forecasts/cdf/',
                        headers=auth_header,
                        base_url=BASE_URL,
                        json=VALID_CDF_FORECAST_JSON)
    assert post.status_code == 201
    new_cdf_fx_url = post.headers['Location']
    get_cdf_fx = sql_api.get(new_cdf_fx_url, headers=auth_header)
    assert get_cdf_fx.status_code == 200
    new_cdf_fx = get_cdf_fx.get_json()

    # Fail to delete site because obs, fx exist for it.
    delete_site = sql_api.delete(new_site_url, headers=auth_header)
    assert delete_site.status_code == 400
    assert new_site in get_site_list(sql_api, auth_header)

    # Delete the created cdf fx
    delete_cdf_fx = sql_api.delete(new_cdf_fx_url, headers=auth_header)
    assert delete_cdf_fx.status_code == 204
    assert new_cdf_fx not in get_cdf_fx_list(sql_api, auth_header)
    assert new_cdf_fx not in get_site_cdf_fx(sql_api, auth_header, new_site_id)

    # Delete the created fx
    delete_fx = sql_api.delete(f'/forecasts/single/{new_fx_id}',
                               headers=auth_header,
                               base_url=BASE_URL)
    assert delete_fx.status_code == 204
    assert new_fx not in get_fx_list(sql_api, auth_header)
    assert new_fx not in get_site_fx(sql_api, auth_header, new_site_id)

    # delete the created obs
    delete_obs = sql_api.delete(f'/observations/{new_obs_id}',
                                headers=auth_header,
                                base_url=BASE_URL)
    assert delete_obs.status_code == 204
    assert new_obs not in get_obs_list(sql_api, auth_header)
    assert new_obs not in get_site_obs(sql_api, auth_header, new_site_id)

    # Delete the site now that we've removed the obs & fx
    delete_site = sql_api.delete(new_site_url, headers=auth_header)
    assert delete_site.status_code == 204
    assert new_site not in get_site_list(sql_api, auth_header)


@pytest.fixture()
def uuid_paths(sql_api):
    paths_with_id = []
    for rule in sql_api.application.url_map.iter_rules():
        if 'GET' in rule.methods and '_id' in rule.rule:
            paths_with_id.append(re.sub('<.+>', '{id}', rule.rule))
    return paths_with_id


@pytest.mark.parametrize('bad_id', [
    '56061aa6-4cf4-11ea-a21d-0a580a800331%',
    'not a real uuid',
])
def test_uuid_path_validation(sql_api, uuid_paths, auth_header, bad_id):
    for path in uuid_paths:
        req = sql_api.get(path.format(id=bad_id),
                          headers=auth_header,
                          base_url=BASE_URL)
        assert req.status_code == 404


@pytest.fixture(scope='module')
def cvtr_testapp(sql_app):
    @sql_app.route('/test/<uuid_str:someuuid>')
    def testroute(someuuid):
        uuid.UUID(someuuid)
        return 'ok'
    yield sql_app


@pytest.mark.parametrize('uuid_str', [
    str(uuid.uuid1()),
    str(uuid.uuid3(uuid.NAMESPACE_DNS, 'solarfarorecastarbiter.org')),
    str(uuid.uuid4()),
    str(uuid.uuid5(uuid.NAMESPACE_DNS, 'solarfarorecastarbiter.org'))
])
def test_uuid_converter_all_versions(cvtr_testapp, uuid_str, auth_header):
    with cvtr_testapp.test_client() as api:
        req = api.get(f'/test/{uuid_str}',
                      headers=auth_header,
                      base_url=BASE_URL)
        assert req.status_code == 200
