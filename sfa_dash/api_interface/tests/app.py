import flask
import sys


test_app = flask.Flask('test')


@test_app.route('/')
def endpnt():
    conf = flask.current_app.config
    i = conf.get('REQS', 0)
    conf['REQS'] = i + 1
    if i > 0:
        return 'OK', 200
    else:
        return 'NO', 503


@test_app.route('/ping')
def ping():
    return 'pong'


@test_app.route('/err')
def err():
    return 'err', 500


@test_app.route('/ok')
def ok():
    return flask.jsonify('ok')


@test_app.route('/badreq')
def bad():
    return '', 405


@test_app.route('/length')
def length():
    conf = flask.current_app.config
    i = conf.get('LREQS', 0)
    conf['LREQS'] = i + 1
    if i > 0:
        return 'OK', 200
    else:
        resp = flask.Response('[]', mimetype='application/json')
        resp.headers.add('content-length', '1000')
        resp.headers.add('transfer-encoding', 'chunked')
        return resp


@test_app.route('/alwaysfail')
def always():
    resp = flask.Response('[]', mimetype='application/json')
    resp.headers.add('content-length', '1000')
    resp.headers.add('transfer-encoding', 'chunked')
    return resp


if __name__ == '__main__':
    test_app.run(port=sys.argv[1])
