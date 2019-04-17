"""Helper functions for all Solar Forecast Arbiter /sites/* endpoints.
"""
from flask import current_app as app


from sfa_dash import oauth_request_session


def get_request(path, **kwargs):
    """Make a get request to a path at SFA api.

    Parameters
    ----------
    path: str
        The api endpoint to query including leading slash.

    Returns
    -------
    requests.Response
        The api response.
    """
    # may need to handle errors if oauth_request_session does not exist somehow
    # definitely need to handle errors here
    return oauth_request_session.get(
        f'{app.config["SFA_API_URL"]}{path}', **kwargs)


def post_request(path, payload, json=True):
    """Post payload to a path at the SFA api.

    Parameters
    ----------
    path: str
        The api endpoint to post to including leading slash.
    payload: str or dict
        Payload to send to the api either a string or JSON dict.
    json: boolean
        A flag for setting the content type of the request, if
        True, posts json to the api, otherwise sends the payload
        as text/csv.

    Returns
    -------
    requests.Response
        The api response.
    """
    if json:
        kwargs = {'json': payload}
    else:
        kwargs = {'headers': {'Content-type': 'text/csv'},
                  'data': payload}
    return oauth_request_session.post(
        f'{app.config["SFA_API_URL"]}{path}', **kwargs)


def delete_request(path, **kwargs):
    """Make a delete request.

    Parameters
    ----------
    path: str
        The api endpoint to post to including leading slash.

    Returns
    -------
    requests.Response
        The api response.
    """
    return oauth_request_session.delete(
        f'{app.config["SFA_API_URL"]}{path}', **kwargs)
