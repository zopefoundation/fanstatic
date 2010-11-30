import py

import webob

from fanstatic import get_current_needed_inclusions

from fanstatic import (Library, ResourceInclusion,
                       init_current_needed_inclusions)
from fanstatic import Inject

from fanstatic import checksum

def test_incorrect_configuration_options():
    app = None
    with py.test.raises(TypeError) as e:
        Inject(app, incorrect='configoption')
    assert (
        "NeededInclusions got an unexpected "
        "keyword argument 'incorrect'") in str(e)

    with py.test.raises(TypeError) as e:
        Inject(app, mode='qux', incorrect='configoption')
    assert (
        "NeededInclusions got an unexpected "
        "keyword argument 'incorrect'") in str(e)

    with py.test.raises(TypeError) as e:
        Inject(app, mode='qux', incorrect='configoption', devmode=True)
    assert (
        "NeededInclusions got an unexpected "
        "keyword argument 'incorrect'") in str(e)

def test_inject():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    def app(environ, start_response):
        start_response('200 OK', [])
        needed = get_current_needed_inclusions()
        needed.need(y1)
        needed.base_url = 'http://testapp'
        return ['<html><head></head><body</body></html>']

    wrapped_app = Inject(app)

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
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        needed = get_current_needed_inclusions()
        needed.need(y1)
        needed.base_url = 'http://testapp'
        return ['<html><head></head><body</body></html>']

    wrapped_app = Inject(app)

    request = webob.Request.blank('/')
    response = request.get_response(wrapped_app)
    assert response.body == '<html><head></head><body</body></html>'

def test_hash_inject():
    pass

