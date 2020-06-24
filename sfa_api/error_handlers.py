from flask import jsonify, current_app
from werkzeug.exceptions import RequestEntityTooLarge


from sfa_api.utils.errors import (BaseAPIException, StorageAuthError,
                                  DeleteRestrictionError)


def base_error_handler(error):
    """Catches any BaseAPIException and formats it correctly.
    """
    return jsonify({'errors': error.errors}), error.status_code


def delete_restriction_handler(error):
    return jsonify({
        'errors': {
            'site': ['Cannot delete site because it is referenced by existing '
                     'forecasts or observations.'],
        }
    }), 400


def auth_existence_handler(error):
    """Immediately returns 404, should be used to catch exceptions when
    a requested resource does not exist, or a user does not have access.
    """
    return jsonify({'errors': {'404': 'Not Found'}}), 404


def entity_too_large_handler(error):
    """Returns a 413 when the content length exceeds maximum"""
    max_payload = current_app.config['MAX_CONTENT_LENGTH']
    return jsonify({
        'errors': {
            '413': f'Payload Too Large. Maximum payload size is {max_payload}'
                   ' bytes.'
        }
    }), 413


def register_error_handlers(app):
    app.register_error_handler(BaseAPIException, base_error_handler)
    app.register_error_handler(StorageAuthError, auth_existence_handler)
    app.register_error_handler(DeleteRestrictionError,
                               delete_restriction_handler)
    app.register_error_handler(RequestEntityTooLarge,
                               entity_too_large_handler)
