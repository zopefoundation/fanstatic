import pytest
import webob

from fanstatic import ConfigurationError
from fanstatic import Fanstatic
from fanstatic import Library
from fanstatic import Resource
from fanstatic import get_needed
from fanstatic import make_serf


def test_inject():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        needed = get_needed()
        needed.need(y1)
        return [b'<html><head></head><body></body></html>']

    wrapped_app = Fanstatic(app, base_url='http://testapp')

    request = webob.Request.blank('/')
    # base_url is defined so SCRIPT_NAME
    request.environ['SCRIPT_NAME'] = '/root'
    # shouldn't be taken into account
    response = request.get_response(wrapped_app)
    assert response.body == b'''\
<html><head><link rel="stylesheet" type="text/css" href="http://testapp/fanstatic/foo/b.css" />
<script type="text/javascript" src="http://testapp/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="http://testapp/fanstatic/foo/c.js"></script></head><body></body></html>'''  # noqa: E501 line too long


def test_inject_script_name():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        needed = get_needed()
        needed.need(y1)
        return [b'<html><head></head><body></body></html>']

    wrapped_app = Fanstatic(app)

    request = webob.Request.blank('/path')
    request.environ['SCRIPT_NAME'] = '/root'
    response = request.get_response(wrapped_app)
    assert response.body == b'''\
<html><head><link rel="stylesheet" type="text/css" href="/root/fanstatic/foo/b.css" />
<script type="text/javascript" src="/root/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/root/fanstatic/foo/c.js"></script></head><body></body></html>'''  # noqa: E501 line too long


def test_incorrect_configuration_options():
    app = None
    with pytest.raises(TypeError) as e:
        Fanstatic(app, incorrect='configoption')
    assert (
        "__init__() got an unexpected "
        "keyword argument 'incorrect'") in str(e)


def test_backward_compatible_configuration_options():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        needed = get_needed()
        needed.need(y1)
        return [b'<html><head></head><body></body></html>']

    wrapped_app = Fanstatic(
        app, base_url='http://testapp',
        bundle=True, minified=True)

    request = webob.Request.blank('/')
    # base_url is defined so SCRIPT_NAME shouldn't be taken into account
    request.environ['SCRIPT_NAME'] = '/root'

    response = request.get_response(wrapped_app)
    assert response.body == b'''\
<html><head><link rel="stylesheet" type="text/css" href="http://testapp/fanstatic/foo/b.css" />
<script type="text/javascript" src="http://testapp/fanstatic/foo/:bundle:a.js;c.js"></script></head><body></body></html>'''  # noqa: E501 line too long


def test_inject_unicode_base_url():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')

    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html;charset=utf-8')])
        x1.need()
        return [b'<html><head></head><body></body></html>']

    request = webob.Request.blank('/')
    wrapped = Fanstatic(app, base_url='http://localhost')
    # Fanstatic used to choke on unicode content.
    request.get_response(wrapped)


def test_serf():
    from fanstatic import get_library_registry
    lib_reg = get_library_registry()
    lib_reg.load_items_from_entry_points()

    pytest.importorskip('mypackage')
    # also test serf config
    d = {
        'resource': 'py:mypackage.style'
    }
    serf = make_serf({}, **d)
    serf = Fanstatic(serf, versioning=False)
    request = webob.Request.blank('/')
    response = request.get_response(serf)
    assert response.body == b'''\
<html><head><link rel="stylesheet" type="text/css" href="/fanstatic/foo/style.css" /></head><body></body></html>'''  # noqa: E501 line too long


def test_serf_unknown_library():
    d = {
        'resource': 'unknown_library:unknown_resource'
    }
    with pytest.raises(ConfigurationError):
        make_serf({}, **d)
