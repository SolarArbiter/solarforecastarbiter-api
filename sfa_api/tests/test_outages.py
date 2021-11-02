import pytest


from sfa_api.conftest import BASE_URL


def outage_exists(outages, expected):
    """Searches a list of outages for an expected outage defined by
    an object with start and end properties.
    """
    for outage in outages:
        if (
            outage['start'] == expected['start']
            and outage['end'] == expected['end']
        ):
            return True
    return False


def test_get_outages(api, addtestsystemoutages):
    req = api.get(
        '/outages/',
        base_url=BASE_URL
    )
    assert req.status_code == 200
    outages = req.get_json()
    the_outage = outages[0]
    assert "outage_id" in the_outage
    assert "created_at" in the_outage
    assert "modified_at" in the_outage
    assert the_outage["start"] == "2019-04-14T07:00:00+00:00"
    assert the_outage["end"] == "2019-04-14T10:00:00+00:00"


@pytest.mark.parametrize("query_args,expected_outages", [
    ({"start": "2019-04-14T10:05Z"},
     [{
        "start": "2019-04-14T10:30:00+00:00",
        "end": "2019-04-14T13:00:00+00:00"
      },
      {
        "start": "2019-04-14T15:00:00+00:00",
        "end": "2019-04-14T17:00:00+00:00"
      }]
     ),
    ({"start": "2019-04-14T11:0Z", "end": "2019-04-14T12:00Z"},
     [{
        "start": "2019-04-14T10:30:00+00:00",
        "end": "2019-04-14T13:00:00+00:00"
      }]
     ),
    ({"end": "2019-04-14T12:00Z"},
     [{
         "start": "2019-04-14T07:00:00+00:00",
         "end": "2019-04-14T10:00:00+00:00"
       },
        {
         "start": "2019-04-14T10:30:00+00:00",
         "end": "2019-04-14T13:00:00+00:00"
        }
      ]
     )
])
def test_get_outages_time_range(
        api, addtestsystemoutages, query_args, expected_outages):
    req = api.get(
        '/outages/',
        base_url=BASE_URL,
        query_string=query_args
    )
    assert req.status_code == 200
    outages = req.get_json()
    for outage in expected_outages:
        assert outage_exists(outages, outage)


@pytest.mark.parametrize("query_args,expected", [
    ({"start": "badtimestamp"}, {"start": ["Invalid start date format"]}),
    ({"end": "badtimestamp"}, {"end": ["Invalid end date format"]}),
])
def test_get_outages_query_errors(
        api, addtestsystemoutages, query_args, expected):
    req = api.get(
        '/outages/',
        base_url=BASE_URL,
        query_string=query_args
    )
    assert req.status_code == 400
    errors = req.get_json()
    assert errors["errors"] == expected
