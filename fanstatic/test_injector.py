from __future__ import with_statement

import pytest

import webob

from fanstatic import (Library, Resource,
                       get_needed, NEEDED)
from fanstatic import Injector

def test_incorrect_configuration_options():
    app = None
    with pytest.raises(TypeError) as e:
        Injector(app, incorrect='configoption')
    assert (
        "__init__() got an unexpected "
        "keyword argument 'incorrect'") in str(e)

    with pytest.raises(TypeError) as e:
        Injector(app, mode='qux', incorrect='configoption')
    assert (
        "__init__() got an unexpected "
        "keyword argument 'incorrect'") in str(e)

    with pytest.raises(TypeError) as e:
        Injector(
            app, mode='qux', incorrect='configoption', recompute_hashes=True)
    assert (
        "__init__() got an unexpected "
        "keyword argument 'incorrect'") in str(e)

def test_inject():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    def app(environ, start_response):
        start_response('200 OK', [])
        needed = get_needed()
        needed.need(y1)
        needed.base_url = 'http://testapp'
        return ['<html><head></head><body</body></html>']

    wrapped_app = Injector(app)

    request = webob.Request.blank('/')
    response = request.get_response(wrapped_app)
    assert response.body == '''\
<html><head>
    <link rel="stylesheet" type="text/css" href="http://testapp/fanstatic/foo/b.css" />
<script type="text/javascript" src="http://testapp/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="http://testapp/fanstatic/foo/c.js"></script>
</head><body</body></html>'''

def test_no_inject_into_non_html():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        needed = get_needed()
        needed.need(y1)
        needed.base_url = 'http://testapp'
        return ['<html><head></head><body</body></html>']

    wrapped_app = Injector(app)

    request = webob.Request.blank('/')
    response = request.get_response(wrapped_app)
    assert response.body == '<html><head></head><body</body></html>'

def test_no_needed_into_non_get_post():
    def app(environ, start_response):
        assert NEEDED not in environ
        start_response('200 OK', [])
        return ['foo']
    wrapped_app = Injector(app)
    request = webob.Request.blank('/', method='PUT')
    request.get_response(wrapped_app)


def test_needed_from_environ():
    def app(environ, start_response):
        start_response('200 OK', [])
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
        return ['']
    wrapped_app = Injector(app)
    request = webob.Request.blank('/', method='GET')
    request.get_response(wrapped_app)
