import pytest


from sfa_api.utils import request_handling


@pytest.mark.parametrize('start,end', [
    ('invalid', 'invalid')
])
def test_validate_start_end_fail(app, forecast_id, start, end):
    with pytest.raises(request_handling.BadAPIRequest):
        with app.test_request_context(
            f'/forecasts/single/{forecast_id}/values?start={start}&end={end}'):
            request_handling.validate_start_end()


@pytest.mark.parametrize('start,end', [
    ('20190101T120000Z','20190101T130000Z')
])
def test_validate_start_end_succexx(app, forecast_id, start, end):
    with app.test_request_context(
        f'/forecasts/single/{forecast_id}/values?start={start}&end={end}'):
        request_handling.validate_start_end()

@pytest.mark.parametrize('content_type,payload', [
    ('text/csv', ''),
    ('application/json', '{}'),
    ('application/json', '{"values": "nope"}'),
    ('text/plain', 'nope'),
])
def test_validate_parsable_fail(app, content_type, payload, forecast_id):
    with pytest.raises(request_handling.BadAPIRequest):
        with app.test_request_context(
            f'/forecasts/single/{forecast_id}/values/',
            content_type=content_type,data=payload,method='POST'):
            request_handling.validate_parsable_values()
