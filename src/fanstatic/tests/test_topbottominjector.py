import pytest

from fanstatic import ConfigurationError
from fanstatic import Library
from fanstatic import Resource
from fanstatic import init_needed
from fanstatic.injector import TopBottomInjector


def test_bundle_resources_bottomsafe():
    foo = Library('foo', '')
    a = Resource(foo, 'a.css')
    b = Resource(foo, 'b.css', bottom=True)

    needed = init_needed(resources=[a, b])

    injector = TopBottomInjector({'bundle': True})
    top, bottom = injector.group(needed)
    assert len(top) == 1
    assert len(bottom) == 0

    injector = TopBottomInjector({'bundle': False, 'bottom': True})
    top, bottom = injector.group(needed)
    assert len(top) == 1
    assert len(bottom) == 1


def test_top_bottom_insert():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    html = b"<html><head>start of head</head><body>rest of body</body></html>"

    needed = init_needed(resources=[y1])

    injector = TopBottomInjector(dict(bottom=True, force_bottom=True))
    assert injector(html, needed) == b'''\
<html><head>start of head<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" /></head><body>rest of body<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script></body></html>'''  # noqa: E501 line too long


def test_html_bottom_safe_used_with_minified():
    foo = Library('foo', '')
    a = Resource(foo, 'a.js', minified='a-minified.js', bottom=True)

    needed = init_needed(resources=[a])

    injector = TopBottomInjector(dict(bottom=True, minified=True))

    with pytest.raises(ConfigurationError):
        TopBottomInjector(dict(debug=True, minified=True))

    top, bottom = injector.group(needed)
    assert len(top) == 0
    assert len(bottom) == 1
    assert bottom.resources[0].relpath == 'a-minified.js'


def test_html_bottom_safe():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])
    y2 = Resource(foo, 'y2.js', bottom=True)

    needed = init_needed(resources=[y1, y2])
    injector = TopBottomInjector({})
    top, bottom = injector.group(needed)
    assert len(top) == 4
    assert len(bottom) == 0

    injector = TopBottomInjector(dict(bottom=True))
    top, bottom = injector.group(needed)
    assert len(top) == 3
    assert len(bottom) == 1
    # The bottom resource is y2.
    assert bottom.resources[0] == y2

    injector = TopBottomInjector(dict(bottom=True, force_bottom=True))
    top, bottom = injector.group(needed)
    assert len(top) == 1
    assert len(bottom) == 3

    top, bottom = injector.group(needed)
    assert len(top) == 1
    assert top.resources[0] == x2
    assert len(bottom) == 3


def test_html_top_bottom_force_bottom():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = init_needed(resources=[y1])
    injector = TopBottomInjector(dict(bottom=True, force_bottom=True))

    top, bottom = injector.group(needed)
    assert top.resources == [x2]
    assert bottom.resources == [x1, y1]


def test_html_top_bottom_set_bottom():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = init_needed(resources=[y1])

    injector = TopBottomInjector(dict(bottom=True))

    top, bottom = injector.group(needed)
    assert len(top) == 3
    assert len(bottom) == 0


def test_html_insert_head_with_attributes():
    # ticket 72: .need() broken when <head> tag has attributes
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    needed = init_needed(resources=[x1])

    injector = TopBottomInjector({})
    html = b'<html><head profile="http://example.org">something</head></html>'
    assert injector(html, needed) == b'''\
<html><head profile="http://example.org">something<script type="text/javascript" src="/fanstatic/foo/a.js"></script></head></html>'''  # noqa: E501 line too long


def test_html_insert():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = init_needed(resources=[y1])

    injector = TopBottomInjector({})
    html = b"<html><head>something more</head></html>"
    assert injector(html, needed) == b'''\
<html><head>something more<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script></head></html>'''  # noqa: E501 line too long
