from flask import jsonify
from sfa_api.utils.errors import BaseAPIException

def base_error_handler(error):
    """
    """
    return jsonify({'errors': error.errors}), error.status_code

def register_error_handlers(app):
    app.register_error_handler(BaseAPIException, base_error_handler)
