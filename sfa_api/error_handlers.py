from flask import jsonify, abort
from sfa_api.utils.errors import (BaseAPIException, StorageAuthError,
                                  DeleteRestrictionError)


def base_error_handler(error):
    """Catches any BaseAPIException and formats it correctly.
    """
    return jsonify({'errors': error.errors}), error.status_code


def delete_restriction_handler(error):
    return jsonify({
        'errors': {
            'site': ['Referenceced by existing forecasts or observations.'],
        }
    }), 400


def auth_existence_handler(error):
    """Immediately returns 404, should be used to catch exceptions when
    a requested resource does not exist, or a user does not have access.
    """
    abort(404)


def register_error_handlers(app):
    app.register_error_handler(BaseAPIException, base_error_handler)
    app.register_error_handler(StorageAuthError, auth_existence_handler)
    app.register_error_handler(DeleteRestrictionError,
                               delete_restriction_handler)
