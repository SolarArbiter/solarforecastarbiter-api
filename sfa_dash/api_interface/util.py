from flask import request, escape

from sfa_dash.errors import DataRequestException


# Utility functions pertaining to interactions with the api.

def handle_response(request_object):
    """Parses the response from a request object. On an a resolvable
    error, raises a DataRequestException with a default error
    message.

    Parameters
    ----------
    request_object: requests.Response
        The response object from an executed request.

    Returns
    -------
    dict, str or None
        Note that this function checks the content-type of a response
        and returns the appropriate type. A Dictionary parsed from a
        JSON object, or a string. Returns None when a 204 is encountered.
        Users should be mindful of the expected response body from the
        API.

    Raises
    ------
    sfa_dash.errors.DataRequestException
        If a recoverable 400 level error has been encountered.
        The errors attribute will contain a dict of errors.
    requests.exceptions.HTTPError
        If the status code received from the API could not be
        handled.
    """
    if not request_object.ok:
        errors = {}
        if request_object.status_code == 400:
            errors = request_object.json()
        elif request_object.status_code == 401:
            errors = {
                '401': "Unauthorized."
            }
        elif request_object.status_code == 404:
            previous_page = request.headers.get('Referer', None)
            errors = {'404': (
                'The requested object could not be found. You may need to '
                'request access from the data owner.')
            }
            if previous_page is not None and previous_page != request.url:
                errors['404'] = errors['404'] + (
                    f' <a href="{escape(previous_page)}">Return to the '
                    'previous page.</a>')
        elif request_object.status_code == 422:
            errors = request_object.json()['errors']
        if errors:
            raise DataRequestException(request_object.status_code, **errors)
        else:
            # Other errors should be due to bugs and not by attempts to reach
            # inaccessible data. Allow exceptions to be raised
            # so that they can be reported to Sentry.
            request_object.raise_for_status()
    if request_object.request.method == 'GET':
        # all GET endpoints should return a JSON object
        if request_object.headers['Content-Type'] == 'application/json':
            return request_object.json()
        else:
            return request_object.text
    # POST responses should contain a single string uuid of a newly created
    # object unless a 204 No Content was returned.
    if request_object.request.method == 'POST':
        if request_object.status_code != 204:
            return request_object.text
