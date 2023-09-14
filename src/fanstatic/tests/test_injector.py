import pytest
import webob

from fanstatic import NEEDED
from fanstatic import Injector
from fanstatic import Library
from fanstatic import Resource
from fanstatic import Slot
from fanstatic import get_needed


def test_incorrect_configuration_options():
    app = None
    with pytest.raises(TypeError) as e:
        Injector(app, incorrect='configoption')
    assert (
        "__init__() got an unexpected "
        "keyword argument 'incorrect'") in str(e)

    with pytest.raises(TypeError) as e:
        Injector(app, mode='qux', incorrect='configoption')
    assert 'keyword argument' in str(e)

    with pytest.raises(TypeError) as e:
        Injector(
            app, mode='qux', incorrect='configoption', recompute_hashes=True)
    assert 'keyword argument' in str(e)


def test_inject():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        needed = get_needed()
        needed.need(y1)
        needed.set_base_url('http://testapp')
        return [b'<html><head></head><body></body></html>']

    wrapped_app = Injector(app)

    request = webob.Request.blank('/')
    response = request.get_response(wrapped_app)
    assert response.body == b'''\
<html><head><link rel="stylesheet" type="text/css" href="http://testapp/fanstatic/foo/b.css" />
<script type="text/javascript" src="http://testapp/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="http://testapp/fanstatic/foo/c.js"></script></head><body></body></html>'''  # noqa: E501 line too long


def test_inject_filled_slot():
    lib = Library('foo', '')
    c = Resource(lib, 'c.js')
    slot = Slot(lib, '.js', depends=[c])
    a = Resource(lib, 'a.js', depends=[slot])
    b = Resource(lib, 'b.js', depends=[c])

    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        needed = get_needed()
        needed.need(a, {slot: b})
        needed.set_base_url('http://testapp')
        return [b'<html><head></head><body></body></html>']

    wrapped_app = Injector(app)

    request = webob.Request.blank('/')
    response = request.get_response(wrapped_app)
    assert response.body == b'''\
<html><head><script type="text/javascript" src="http://testapp/fanstatic/foo/c.js"></script>
<script type="text/javascript" src="http://testapp/fanstatic/foo/b.js"></script>
<script type="text/javascript" src="http://testapp/fanstatic/foo/a.js"></script></head><body></body></html>'''  # noqa: E501 line too long


def test_needed_deleted_after_request():
    def html_app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        assert NEEDED in environ
        return [b'<html><head></head><body></body></html>']

    wrapped_app = Injector(html_app)
    request = webob.Request.blank('/')
    request.get_response(wrapped_app)
    # There's no NeededResources object anymore after the request has
    # been done.
    dummy = get_needed()
    with pytest.raises(NotImplementedError):
        dummy.clear()

    def textplain_app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        assert NEEDED in environ
        return [b'<html><head></head><body></body></html>']

    wrapped_app = Injector(textplain_app)
    request = webob.Request.blank('/')
    request.get_response(wrapped_app)
    # There's no NeededResources object anymore after the request has
    # been done, even for response content types that would not have
    # been processed by fanstatic's inclusion rendering.
    dummy = get_needed()
    with pytest.raises(NotImplementedError):
        dummy.clear()


def test_no_inject_into_non_html():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        needed = get_needed()
        needed.need(y1)
        return [b'<html><head></head><body></body></html>']

    wrapped_app = Injector(app)

    request = webob.Request.blank('/')
    response = request.get_response(wrapped_app)
    assert response.body == b'<html><head></head><body></body></html>'


def test_no_needed_into_non_get_post():
    def app(environ, start_response):
        assert NEEDED not in environ
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [b'foo']
    wrapped_app = Injector(app)
    request = webob.Request.blank('/', method='PUT')
    request.get_response(wrapped_app)


def test_needed_from_environ():
    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        needed = get_needed()
        assert needed is environ[NEEDED]

    wrapped_app = Injector(app)
    request = webob.Request.blank('/')
    request.get_response(wrapped_app)


def test_can_handle_no_content():
    foo = Library('foo', '')
    Resource(foo, 'a.js')

    def app(environ, start_response):
        # if no header is given, we get a defailt content type
        # header and won't trigger the fault from
        # https://bitbucket.org/fanstatic/fanstatic/issue/49/exception-in-injector-when-app-returns-304
        start_response('304 Not Modified', [('fake', '123')])
        return [b'']
    wrapped_app = Injector(app)
    request = webob.Request.blank('/', method='GET')
    request.get_response(wrapped_app)
