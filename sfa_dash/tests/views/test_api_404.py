import pytest


from sfa_dash.conftest import BASE_URL, site_id_route_list


@pytest.fixture
def dne_uuid():
    return 'b6984bb8-9930-11ea-8541-54be64636445'


@pytest.mark.parametrize('route', [
    '/observations/',
    '/forecasts/single/',
    '/forecasts/cdf/',
])
def test_listing_filter_bad_site(client, route, dne_uuid):
    resp = client.get(route, base_url=BASE_URL,
                      query_string={'site_id': dne_uuid})
    assert "<b>404: </b>" in resp.data.decode('utf-8')


@pytest.mark.parametrize('route', [
    '/observations/',
    '/forecasts/single/',
    '/forecasts/cdf/',
])
def test_listing_filter_bad_aggregate(client, route, dne_uuid):
    resp = client.get(route, base_url=BASE_URL,
                      query_string={'aggregate_id': dne_uuid})
    assert "<b>404: </b>" in resp.data.decode('utf-8')


def test_get_observation_routes(client, observation_id_route, dne_uuid):
    resp = client.get(observation_id_route(dne_uuid), base_url=BASE_URL)
    assert "<b>404: </b>" in resp.data.decode('utf-8')


def test_get_forecast_routes(client, forecast_id_route, dne_uuid):
    resp = client.get(forecast_id_route(dne_uuid), base_url=BASE_URL)
    assert "<b>404: </b>" in resp.data.decode('utf-8')


@pytest.fixture(params=[route for route in site_id_route_list
                        if 'create' not in route])
def site_route(request):
    def fn(site_id):
        return request.param.format(site_id=site_id)
    return fn


def test_get_site_routes(client, site_route, dne_uuid):
    resp = client.get(site_route(dne_uuid), base_url=BASE_URL)
    assert "<b>404: </b>" in resp.data.decode('utf-8')


@pytest.fixture(params=[route for route in site_id_route_list
                        if 'create' in route])
def create_at_site_route(request):
    def fn(site_id):
        return request.param.format(site_id=site_id)
    return fn


def test_get_create_at_site_routes(client, create_at_site_route, dne_uuid):
    resp = client.get(create_at_site_route(dne_uuid), base_url=BASE_URL,
                      follow_redirects=True)
    assert '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')


def test_get_cdf_forecast_routes(
        client, cdf_forecast_id_route, dne_uuid):
    resp = client.get(cdf_forecast_id_route(dne_uuid),
                      base_url=BASE_URL)
    assert "<b>404: </b>" in resp.data.decode('utf-8')


@pytest.fixture()
def multiarg_uuids(
        permission_id, role_id, user_id, valid_permission_object_id):
    return {
        'permission_id': permission_id,
        'role_id': role_id,
        'user_id': user_id,
        'object_id': valid_permission_object_id,
    }


def test_remove_object_from_perm(client, multiarg_uuids, dne_uuid):
    route = '/admin/permissions/{permission_id}/remove/{object_id}'
    for route_key in ['permission_id', 'object_id']:
        fkwargs = multiarg_uuids.copy()
        fkwargs[route_key] = dne_uuid
        resp = client.get(route.format(**fkwargs), base_url=BASE_URL)
        contains_404 = (
            "<b>404: </b>" in resp.data.decode('utf-8') or
            '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
        )
        assert contains_404


def test_remove_perm_from_role(client, multiarg_uuids, dne_uuid):
    route = '/admin/roles/{role_id}/remove/{permission_id}'
    for route_key in ['permission_id', 'role_id']:
        fkwargs = multiarg_uuids.copy()
        fkwargs[route_key] = dne_uuid
        resp = client.get(route.format(**fkwargs), base_url=BASE_URL)
        contains_404 = (
            "<b>404: </b>" in resp.data.decode('utf-8') or
            '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
        )
        assert contains_404


def test_remove_role_from_user_invalid_role(client, multiarg_uuids, dne_uuid):
    route = '/admin/users/{user_id}/remove/{role_id}'
    fkwargs = multiarg_uuids.copy()
    fkwargs['role_id'] = dne_uuid
    resp = client.get(route.format(**fkwargs), base_url=BASE_URL,
                      follow_redirects=True)
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert contains_404


def test_remove_role_from_user_user_unreadable(
        client, multiarg_uuids, dne_uuid):
    route = '/admin/users/{user_id}/remove/{role_id}'
    fkwargs = multiarg_uuids.copy()
    fkwargs['user_id'] = dne_uuid
    resp = client.get(route.format(**fkwargs), base_url=BASE_URL)
    assert (
        '<div class="alert alert-warning" role="alert">It appears you do not '
        'have access to read the metadata of this user'
        in resp.data.decode('utf-8'))


def test_user_id_routes(client, user_id_route, dne_uuid):
    resp = client.get(user_id_route(dne_uuid), base_url=BASE_URL)
    assert "<b>404: </b>" in resp.data.decode('utf-8')


def test_permission_id_routes(client, permission_id_route, dne_uuid):
    resp = client.get(permission_id_route(dne_uuid), base_url=BASE_URL)
    assert "<b>404: </b>" in resp.data.decode('utf-8')


def test_role_id_routes(client, role_id_route, dne_uuid):
    resp = client.get(role_id_route(dne_uuid), base_url=BASE_URL)
    assert "<b>404: </b>" in resp.data.decode('utf-8')


def test_aggregate_id_routes(client, aggregate_id_route, dne_uuid):
    resp = client.get(aggregate_id_route(dne_uuid), base_url=BASE_URL,
                      follow_redirects=True)
    contains_404 = (
            "<b>404: </b>" in resp.data.decode('utf-8') or
            '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
        )
    assert contains_404


def test_report_id_routes(client, report_id_route, dne_uuid):
    resp = client.get(report_id_route(dne_uuid), base_url=BASE_URL)
    assert "<b>404: </b>" in resp.data.decode('utf-8')


def test_clone_routes(client, clone_route, missing_id):
    ids = {
        'forecast_id': missing_id,
        'observation_id': missing_id,
        'site_id': missing_id
    }
    resp = client.get(clone_route(ids), base_url=BASE_URL,
                      follow_redirects=True)
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert contains_404
