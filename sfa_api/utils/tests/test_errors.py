import pytest


from sfa_api.utils.errors import BaseAPIException, NotFoundException, BadAPIRequest


error_dict = {'error': 'message',
              'error2': ['message'],
              'error3': ('went', 'wrong')}
def test_baseapiexception_dict():
    exc = BaseAPIException(400, error_dict)
    assert exc.status_code == 400
    assert exc.errors['error'] == ['message']
    assert exc.errors['error2'] == ['message']
    assert exc.errors['error3'] == [('went', 'wrong')]


def test_baseapiexception_kwargs():
    exc = BaseAPIException(782, **error_dict)
    assert exc.status_code == 782
    assert exc.errors['error'] == ['message']
    assert exc.errors['error2'] == ['message']
    assert exc.errors['error3'] == [('went', 'wrong')]

def test_badapirequest_dict():
    exc = BadAPIRequest(error_dict)
    assert exc.status_code == 400
    assert exc.errors['error'] == ['message']
    assert exc.errors['error2'] == ['message']
    assert exc.errors['error3'] == [('went', 'wrong')]


def test_basapirequest_kwargs():
    exc = BadAPIRequest(error_dict)
    assert exc.status_code == 400
    assert exc.errors['error'] == ['message']
    assert exc.errors['error2'] == ['message']
    assert exc.errors['error3'] == [('went', 'wrong')]


def test_notfoundexception():
    exc = NotFoundException(thing="Couldn't find it.")
    assert exc.status_code == 404
    assert exc.errors['thing'] == ["Couldn't find it."]
