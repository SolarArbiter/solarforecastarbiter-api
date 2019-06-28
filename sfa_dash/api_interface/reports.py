from flask import abort
from flask import current_app as app
from requests.exceptions import HTTPError

from sfa_dash import oauth_request_session
from solarforecastarbiter.io.api import APISession


def _get_session():
    token = oauth_request_session.token['access_token']
    session = APISession(token, base_url=app.config['SFA_API_URL'])
    return session


def get_metadata(report_id):
    try:
        session = _get_session()
        report = session.get_report(report_id)
    except HTTPError:
        abort(404)
    return report


def list_full_reports():
    try:
        session = _get_session()
        report = session.get('/reports/')
    except HTTPError:
        abort(404)
    else:
        return report.json()


def list_metadata():
    try:
        session = _get_session()
        reports = session.list_reports()
    except HTTPError:
        abort(404)
    return reports


def post_metadata(report_dict):
    session = _get_session()
    post_request = session.post('/reports/', json=report_dict)
    return post_request


def delete(report_id):
    session = _get_session()
    delete = session.delete(f'/reports/{report_id}')
    return delete
