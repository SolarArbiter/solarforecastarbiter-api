from sfa_dash.conftest import BASE_URL


def test_get_no_arg_routes(client, no_arg_route):
    resp = client.get(no_arg_route, base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_site_filtered_no_args(client, no_arg_route, site_id):
    resp = client.get(no_arg_route, base_url=BASE_URL,
                      data={'site_id': site_id})
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_aggregate_filtered_no_args(client, no_arg_route, aggregate_id):
    resp = client.get(no_arg_route, base_url=BASE_URL,
                      data={'aggregate_id': aggregate_id})
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_get_observation_routes(client, observation_id_route, observation_id):
    resp = client.get(observation_id_route(observation_id), base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_get_forecast_routes(client, forecast_id_route, forecast_id):
    resp = client.get(forecast_id_route(forecast_id), base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_get_site_routes(client, site_id_route, site_id):
    resp = client.get(site_id_route(site_id), base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_get_cdf_forecast_routes(
        client, cdf_forecast_id_route, cdf_forecast_group_id):
    resp = client.get(cdf_forecast_id_route(cdf_forecast_group_id),
                      base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_get_cdf_forecast_single_routes(
        client, cdf_forecast_single_id_route, cdf_forecast_id):
    resp = client.get(cdf_forecast_single_id_route(cdf_forecast_id),
                      base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_admin_route_list(client, admin_route):
    resp = client.get(admin_route, base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_admin_multiarg_route_list(
        client, admin_multiarg_route, permission_id, role_id, user_id,
        valid_permission_object_id):
    resp = client.get(
        admin_multiarg_route(
            valid_permission_object_id,
            permission_id,
            user_id,
            role_id),
        base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_user_id_routes(client, user_id_route, user_id):
    resp = client.get(user_id_route(user_id), base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_permission_id_routes(client, permission_id_route, permission_id):
    resp = client.get(permission_id_route(permission_id), base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_role_id_routes(client, role_id_route, role_id):
    resp = client.get(role_id_route(role_id), base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_aggregate_id_routes(client, aggregate_id_route, aggregate_id):
    resp = client.get(aggregate_id_route(aggregate_id), base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404


def test_report_id_routes(client, report_id_route, report_id):
    resp = client.get(report_id_route(report_id), base_url=BASE_URL)
    assert resp.status_code == 200
    contains_404 = (
        "<b>404: </b>" in resp.data.decode('utf-8') or
        '<li class="alert alert-danger">(404)' in resp.data.decode('utf-8')
    )
    assert not contains_404
