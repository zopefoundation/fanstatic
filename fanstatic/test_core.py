from __future__ import with_statement

import pytest

from fanstatic import (Library,
                       Resource,
                       NeededResources,
                       GroupResource,
                       init_needed,
                       get_needed,
                       clear_needed,
                       register_inclusion_renderer,
                       sort_resources_topological,
                       ConfigurationError,
                       UnknownResourceExtension)

from fanstatic.core import inclusion_renderers, normalize_resource


def test_resource():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = NeededResources()
    needed.need(y1)

    assert needed.resources() == [x2, x1, y1]

def test_group_resource():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    group = GroupResource([x1, x2])

    needed = NeededResources()
    needed.need(group)

    assert group.resources() == [x1, x2]

    more_stuff = Resource(foo, 'more_stuff.js', depends=[group])
    assert more_stuff.resources() == [x1, x2, more_stuff]

def test_convenience_need_not_initialized():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    dummy = get_needed()
    assert not isinstance(dummy, NeededResources)

    # We return a new dummy instance for every get_needed:
    dummy2 = get_needed()
    assert dummy != dummy2

    dummy.need(y1)
    with pytest.raises(NotImplementedError):
        dummy.render()

def test_convenience_clear_not_initialized():
    # This test is put near the top of this module, or at least before
    # the very first time ``init_needed()`` is called.
    dummy = get_needed()
    with pytest.raises(NotImplementedError):
        dummy.clear()
    with pytest.raises(NotImplementedError):
        clear_needed()

def test_convenience_need():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = init_needed()
    assert get_needed() == needed
    assert get_needed().resources() == []

    y1.need()

    assert get_needed().resources() == [x2, x1, y1]

def test_convenience_group_resource_need():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js')
    group = GroupResource([x1, x2, y1])

    needed = init_needed()
    assert get_needed() == needed
    assert get_needed().resources() == []

    group.need()

    assert get_needed().resources() == [x2, x1, y1]

def test_redundant_resource():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = NeededResources()

    needed.need(y1)
    needed.need(y1)
    assert needed.resources() == [x2, x1, y1]

    needed.need(x1)
    assert needed.resources() == [x2, x1, y1]

    needed.need(x2)
    assert needed.resources() == [x2, x1, y1]

def test_redundant_resource_reorder():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = NeededResources()
    needed.need(x1)
    needed.need(x2)
    needed.need(y1)
    assert needed.resources() == [x2, x1, y1]

def test_redundant_more_complicated():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    a2 = Resource(foo, 'a2.js', depends=[a1])
    a3 = Resource(foo, 'a3.js', depends=[a2])
    a4 = Resource(foo, 'a4.js', depends=[a1])

    needed = NeededResources()
    needed.need(a3)
    assert needed.resources() == [a1, a2, a3]
    needed.need(a4)
    assert needed.resources() == [a1, a2, a3, a4]

def test_redundant_more_complicated_reversed():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    a2 = Resource(foo, 'a2.js', depends=[a1])
    a3 = Resource(foo, 'a3.js', depends=[a2])
    a4 = Resource(foo, 'a4.js', depends=[a1])

    needed = NeededResources()
    needed.need(a4)
    needed.need(a3)

    assert needed.resources() == [a1, a4, a2, a3]

def test_redundant_more_complicated_depends_on_all():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    a2 = Resource(foo, 'a2.js', depends=[a1])
    a3 = Resource(foo, 'a3.js', depends=[a2])
    a4 = Resource(foo, 'a4.js', depends=[a1])
    a5 = Resource(foo, 'a5.js', depends=[a4, a3])

    needed = NeededResources()
    needed.need(a5)

    assert needed.resources() == [a1, a4, a2, a3, a5]

def test_redundant_more_complicated_depends_on_all_reorder():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    a2 = Resource(foo, 'a2.js', depends=[a1])
    a3 = Resource(foo, 'a3.js', depends=[a2])
    a4 = Resource(foo, 'a4.js', depends=[a1])
    a5 = Resource(foo, 'a5.js', depends=[a4, a3])

    needed = NeededResources()
    needed.need(a3)
    needed.need(a5)

    assert needed.resources() == [a1, a2, a3, a4, a5]

def test_mode_fully_specified():
    foo = Library('foo', '')
    k_debug = Resource(foo, 'k-debug.js')
    k = Resource(foo, 'k.js', debug=k_debug)

    needed = NeededResources()
    needed.need(k)

    assert needed.resources() == [k]

    needed = NeededResources(debug=True)
    needed.need(k)

    assert needed.resources() == [k_debug]

    with pytest.raises(ConfigurationError):
        NeededResources(debug=True, minified=True)

def test_mode_shortcut():
    foo = Library('foo', '')
    k = Resource(foo, 'k.js', debug='k-debug.js')

    needed = NeededResources()
    needed.need(k)

    assert needed.resources() == [k]

    needed = NeededResources(debug=True)
    needed.need(k)

    assert len(needed.resources()) == 1
    assert needed.resources()[0].relpath == 'k-debug.js'

def test_rollup():
    foo = Library('foo', '')
    b1 = Resource(foo, 'b1.js')
    b2 = Resource(foo, 'b2.js')
    giant = Resource(foo, 'giant.js', supersedes=[b1, b2])

    needed = NeededResources(rollup=True)
    needed.need(b1)
    needed.need(b2)

    assert needed.resources() == [giant]

def test_rollup_cannot():
    foo = Library('foo', '')
    b1 = Resource(foo, 'b1.js')
    b2 = Resource(foo, 'b2.js')

    giant = Resource(foo, 'giant.js', supersedes=[b1, b2])

    needed = NeededResources(rollup=True)
    needed.need(b1)
    assert needed.resources() == [b1]
    assert giant not in needed.resources()

def test_rollup_larger():
    foo = Library('foo', '')
    c1 = Resource(foo, 'c1.css')
    c2 = Resource(foo, 'c2.css')
    c3 = Resource(foo, 'c3.css')
    giant = Resource(foo, 'giant.css', supersedes=[c1, c2, c3])

    needed = NeededResources(rollup=True)
    needed.need(c1)

    assert needed.resources() == [c1]

    needed.need(c2)

    assert needed.resources() == [c1, c2]

    needed.need(c3)

    assert needed.resources() == [giant]

def test_rollup_eager():
    foo = Library('foo', '')
    d1 = Resource(foo, 'd1.js')
    d2 = Resource(foo, 'd2.js')
    d3 = Resource(foo, 'd3.js')
    giant = Resource(foo, 'giant.js', supersedes=[d1, d2, d3],
                     eager_superseder=True)

    needed = NeededResources(rollup=True)
    needed.need(d1)
    assert needed.resources() == [giant]

    needed = NeededResources(rollup=True)
    needed.need(d1)
    needed.need(d2)
    assert needed.resources() == [giant]

def test_rollup_eager_competing():
    foo = Library('foo', '')
    d1 = Resource(foo, 'd1.js')
    d2 = Resource(foo, 'd2.js')
    d3 = Resource(foo, 'd3.js')
    d4 = Resource(foo, 'd4.js')
    giant = Resource(foo, 'giant.js', supersedes=[d1, d2, d3],
                     eager_superseder=True)
    giant_bigger = Resource(foo, 'giant-bigger.js',
                            supersedes=[d1, d2, d3, d4],
                            eager_superseder=True)

    needed = NeededResources(rollup=True)
    needed.need(d1)
    assert needed.resources() == [giant_bigger]
    assert giant not in needed.resources()

def test_rollup_eager_noneager_competing():
    foo = Library('foo', '')
    d1 = Resource(foo, 'd1.js')
    d2 = Resource(foo, 'd2.js')
    d3 = Resource(foo, 'd3.js')
    giant = Resource(foo, 'giant.js', supersedes=[d1, d2, d3],
                     eager_superseder=True)
    giant_noneager = Resource(foo, 'giant-noneager.js',
                              supersedes=[d1, d2, d3])
    needed = NeededResources(rollup=True)
    needed.need(d1)
    assert needed.resources() == [giant]
    assert giant_noneager not in needed.resources()

def test_rollup_size_competing():
    foo = Library('foo', '')
    d1 = Resource(foo, 'd1.js')
    d2 = Resource(foo, 'd2.js')
    d3 = Resource(foo, 'd3.js')
    giant = Resource(foo, 'giant.js', supersedes=[d1, d2])
    giant_bigger = Resource(foo, 'giant-bigger.js',
                            supersedes=[d1, d2, d3])

    needed = NeededResources(rollup=True)
    needed.need(d1)
    needed.need(d2)
    needed.need(d3)
    assert needed.resources() == [giant_bigger]
    assert giant not in needed.resources()

def test_rollup_eager_noneager_size_competing():
    foo = Library('foo', '')
    d1 = Resource(foo, 'd1.js')
    d2 = Resource(foo, 'd2.js')
    d3 = Resource(foo, 'd3.js')
    d4 = Resource(foo, 'd4.js')
    giant = Resource(foo, 'giant.js', supersedes=[d1, d2, d3],
                     eager_superseder=True)
    giant_noneager_bigger = Resource(foo, 'giant-noneager.js',
                                     supersedes=[d1, d2, d3, d4])
    needed = NeededResources(rollup=True)
    needed.need(d1)
    assert needed.resources() == [giant]
    assert giant_noneager_bigger not in needed.resources()

def test_rollup_modes():
    foo = Library('foo', '')
    f1 = Resource(foo, 'f1.js', debug='f1-debug.js')
    f2 = Resource(foo, 'f2.js', debug='f2-debug.js')
    giantf = Resource(foo, 'giantf.js', supersedes=[f1, f2],
                      debug='giantf-debug.js')

    needed = NeededResources(rollup=True)
    needed.need(f1)
    needed.need(f2)
    assert needed.resources() == [giantf]

    needed = NeededResources(rollup=True, debug=True)
    needed.need(f1)
    needed.need(f2)
    assert len(needed.resources()) == 1
    assert needed.resources()[0].relpath == 'giantf-debug.js'

def test_rollup_meaningless_rollup_mode():
    foo = Library('foo', '')
    g1 = Resource(foo, 'g1.js')
    g2 = Resource(foo, 'g2.js')
    giantg = Resource(foo, 'giantg.js', supersedes=[g1, g2],
                      debug='giantg-debug.js')
    needed = NeededResources(rollup=True)
    needed.need(g1)
    needed.need(g2)
    assert needed.resources() == [giantg]

    needed = NeededResources(rollup=True, debug=True)
    needed.need(g1)
    needed.need(g2)
    assert needed.resources() == [giantg]

def test_rollup_without_mode():
    foo = Library('foo', '')
    h1 = Resource(foo, 'h1.js', debug='h1-debug.js')
    h2 = Resource(foo, 'h2.js', debug='h2-debug.js')
    gianth = Resource(foo, 'gianth.js', supersedes=[h1, h2])

    needed = NeededResources(rollup=True)
    needed.need(h1)
    needed.need(h2)
    assert needed.resources() == [gianth]

    needed = NeededResources(rollup=True, debug=True)
    needed.need(h1)
    needed.need(h2)
    # no mode available for rollup
    assert len(needed.resources()) == 2
    assert needed.resources()[0].relpath == 'h1-debug.js'
    assert needed.resources()[1].relpath == 'h2-debug.js'

def test_rendering():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = NeededResources(base_url='')
    needed.need(y1)

    assert needed.render() == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''

def test_rendering_base_url():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = NeededResources()
    needed.need(y1)
    with pytest.raises(ConfigurationError):
        needed.render()

    # We need a base_url in order to render URLs to resources.
    needed.base_url = ''
    assert needed.render() == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''

    needed = NeededResources(base_url='http://localhost/static')
    needed.need(y1)
    assert needed.render() == '''\
<link rel="stylesheet" type="text/css" href="http://localhost/static/fanstatic/foo/b.css" />
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/c.js"></script>'''

def test_empty_base_url_and_publisher_signature():
    ''' When the base_url and publisher_signature are both empty strings,
    render a URL without them. '''
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    needed = NeededResources(base_url='', publisher_signature='')
    needed.need(x1)

    assert needed.render() == '''\
<script type="text/javascript" src="/foo/a.js"></script>'''

def test_rendering_base_url_assign():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = NeededResources()
    needed.need(y1)

    needed.base_url = 'http://localhost/static'

    assert needed.render() == '''\
<link rel="stylesheet" type="text/css" href="http://localhost/static/fanstatic/foo/b.css" />
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/c.js"></script>'''


def test_library_url_default_publisher_signature():
    foo = Library('foo', '')

    needed = NeededResources(base_url='')

    assert needed.library_url(foo) == '/fanstatic/foo'

def test_library_url_publisher_signature():
    foo = Library('foo', '')

    needed = NeededResources(base_url='', publisher_signature='waku')

    assert needed.library_url(foo) == '/waku/foo'

def test_library_url_base_url():
    foo = Library('foo', '')

    needed = NeededResources(base_url="http://example.com/something")

    assert (needed.library_url(foo) ==
            'http://example.com/something/fanstatic/foo')

def test_library_url_version_hashing(tmpdir):
    foo = Library('foo', tmpdir.strpath)

    needed = NeededResources(base_url='', versioning=True)

    assert (needed.library_url(foo) ==
            '/fanstatic/foo/:version:d41d8cd98f00b204e9800998ecf8427e')

    bar = Library('bar', '', version='1')
    assert (needed.library_url(bar) == '/fanstatic/bar/:version:1')

def test_library_url_hashing_norecompute(tmpdir):
    foo = Library('foo', tmpdir.strpath)

    needed = NeededResources(
        base_url='', versioning=True, recompute_hashes=False)

    url = needed.library_url(foo)

    # now create a file
    resource = tmpdir.join('test.js')
    resource.write('/* test */')

    # since we're not re-computing hashes, the hash in the URL won't change
    assert needed.library_url(foo) == url

def test_library_url_hashing_recompute(tmpdir):
    foo = Library('foo', tmpdir.strpath)

    needed = NeededResources(
        base_url='', versioning=True, recompute_hashes=True)

    url = needed.library_url(foo)

    # now create a file
    resource = tmpdir.join('test.js')
    resource.write('/* test */')

    # the hash is recalculated now, so it changes
    assert needed.library_url(foo) != url

def test_html_insert():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = NeededResources(base_url='')
    needed.need(y1)

    html = "<html><head>something more</head></html>"

    # XXX where is extraneous space coming from? misguided attempt at
    # indentation?
    assert needed.render_into_html(html) == '''\
<html><head>
    <link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>
something more</head></html>'''

def test_html_top_bottom():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = NeededResources(base_url='')
    needed.need(y1)

    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''
    assert bottom == ''

def test_html_top_bottom_set_bottom():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = NeededResources(base_url='', bottom=True)
    needed.need(y1)

    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''
    assert bottom == ''

def test_html_top_bottom_force_bottom():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = NeededResources(base_url='', bottom=True, force_bottom=True)
    needed.need(y1)

    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />'''
    assert bottom == '''\
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''


def test_html_bottom_safe():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])
    y2 = Resource(foo, 'y2.js', bottom=True)

    needed = NeededResources(base_url='')
    needed.need(y1)
    needed.need(y2)
    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>
<script type="text/javascript" src="/fanstatic/foo/y2.js"></script>'''
    assert bottom == ''

    needed = NeededResources(base_url='', bottom=True)
    needed.need(y1)
    needed.need(y2)
    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''
    assert bottom == '''\
<script type="text/javascript" src="/fanstatic/foo/y2.js"></script>'''

    needed = NeededResources(base_url='', bottom=True, force_bottom=True)
    needed.need(y1)
    needed.need(y2)
    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />'''
    assert bottom == '''\
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>
<script type="text/javascript" src="/fanstatic/foo/y2.js"></script>'''

# XXX add sanity checks: cannot declare something bottom safe while
# what it depends on isn't bottom safe


def test_top_bottom_insert():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    html = "<html><head>rest of head</head><body>rest of body</body></html>"

    needed = NeededResources(base_url='', bottom=True, force_bottom=True)
    needed.need(y1)
    assert needed.render_topbottom_into_html(html) == '''\
<html><head>
    <link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
rest of head</head><body>rest of body<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script></body></html>'''

def test_sorting_resources():
    foo = Library('foo', '')

    a1 = Resource(foo, 'a1.js')
    a2 = Resource(foo, 'a2.js', depends=[a1])
    a3 = Resource(foo, 'a3.js', depends=[a2])
    a4 = Resource(foo, 'a4.js', depends=[a1])
    a5 = Resource(foo, 'a5.js', depends=[a4, a3])

    assert sort_resources_topological([a5, a3, a1, a2, a4]) == [
        a1, a4, a2, a3, a5]

def test_inclusion_renderers():
    assert sorted(
        [(order, key) for key, (order, _) in inclusion_renderers.items()]) == [
        (10, '.css'), (20, '.js'), (30, '.ico')]
    _, renderer = inclusion_renderers['.js']
    assert renderer('http://localhost/script.js') == (
         '<script type="text/javascript" src="http://localhost/script.js"></script>')

def test_register_inclusion_renderer():
    foo = Library('foo', '')

    with pytest.raises(UnknownResourceExtension):
        # The renderer for '.unknown' is not yet defined.
        Resource(foo, 'nothing.unknown')

    def render_unknown(url):
        return '<link rel="unknown" href="%s" />' % url

    register_inclusion_renderer('.unknown', render_unknown)
    a = Resource(foo, 'nothing.unknown')

    needed = NeededResources(base_url='')
    needed.need(a)
    assert needed.render() == ('<link rel="unknown" href="/fanstatic/foo/nothing.unknown" />')

def test_registered_inclusion_renderers_in_order():
    foo = Library('foo', '')

    def render_unknown(url):
        return '<unknown href="%s"/>' % url

    register_inclusion_renderer('.later', render_unknown, 50)
    a = Resource(foo, 'nothing.later')
    b = Resource(foo, 'something.js')
    c = Resource(foo, 'something.css')
    d = Resource(foo, 'something.ico')

    needed = NeededResources(base_url='')
    needed.need(a)
    needed.need(b)
    needed.need(c)
    needed.need(d)

    assert needed.render() == """\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/something.css" />
<script type="text/javascript" src="/fanstatic/foo/something.js"></script>
<link rel="shortcut icon" type="image/x-icon" href="/fanstatic/foo/something.ico"/>
<unknown href="/fanstatic/foo/nothing.later"/>"""

    register_inclusion_renderer('.sooner', render_unknown, 5)
    e = Resource(foo, 'nothing.sooner')
    needed.need(e)
    assert needed.render() == """\
<unknown href="/fanstatic/foo/nothing.sooner"/>
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/something.css" />
<script type="text/javascript" src="/fanstatic/foo/something.js"></script>
<link rel="shortcut icon" type="image/x-icon" href="/fanstatic/foo/something.ico"/>
<unknown href="/fanstatic/foo/nothing.later"/>"""

    register_inclusion_renderer('.between', render_unknown, 25)
    f = Resource(foo, 'nothing.between')
    needed.need(f)
    assert needed.render() == """\
<unknown href="/fanstatic/foo/nothing.sooner"/>
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/something.css" />
<script type="text/javascript" src="/fanstatic/foo/something.js"></script>
<unknown href="/fanstatic/foo/nothing.between"/>
<link rel="shortcut icon" type="image/x-icon" href="/fanstatic/foo/something.ico"/>
<unknown href="/fanstatic/foo/nothing.later"/>"""

def test_custom_renderer_for_resource():
    foo = Library('foo', '')

    def render_print_css(url):
        return ('<link rel="stylesheet" type="text/css" href="%s" media="print"/>' %
                url)

    a = Resource(foo, 'printstylesheet.css', renderer=render_print_css)
    needed = NeededResources(base_url='')
    needed.need(a)
    assert needed.render() == """\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/printstylesheet.css" media="print"/>"""

    def render_unknown(url):
        return '<unknown href="%s"/>' % url

    b = Resource(foo, 'nothing.unknown', renderer=render_unknown)
    needed.need(b)
    assert needed.render() == """\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/printstylesheet.css" media="print"/>
<unknown href="/fanstatic/foo/nothing.unknown"/>"""

def test_custom_renderer_keep_together():
    foo = Library('foo', '')

    def render_print_css(url):
        return ('<link rel="stylesheet" type="text/css" href="%s" media="print"/>' %
                url)

    a = Resource(foo, 'printstylesheet.css', renderer=render_print_css)
    b = Resource(foo, 'regular.css')
    c = Resource(foo, 'something.js')

    needed = NeededResources(base_url='')
    needed.need(a)
    needed.need(b)
    needed.need(c)

    assert needed.render() == """\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/printstylesheet.css" media="print"/>
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/regular.css" />
<script type="text/javascript" src="/fanstatic/foo/something.js"></script>"""

def test_resource_subclass_render():
    foo = Library('foo', '')
    class MyResource(Resource):
        def render(self, library_url):
            return '<myresource reference="%s/%s"/>' % (library_url, self.relpath)

    a = MyResource(foo, 'printstylesheet.css')
    needed = NeededResources(base_url='')
    needed.need(a)
    assert needed.render() == """\
<myresource reference="/fanstatic/foo/printstylesheet.css"/>"""

def test_clear():
    foo = Library('foo', '')

    a1 = Resource(foo, 'a1.js')
    a2 = Resource(foo, 'a2.js', depends=[a1])
    a3 = Resource(foo, 'a3.js', depends=[a2])

    a4 = Resource(foo, 'a4.js', depends=[a1])
    a5 = Resource(foo, 'a5.js', depends=[a4, a3])

    needed = NeededResources()
    needed.need(a1)
    needed.need(a2)
    needed.need(a3)
    assert needed.resources() == [a1, a2, a3]
    # For some reason,for example an error page needs to be rendered,
    # the currently needed resources need to be cleared.
    needed.clear()
    assert needed.resources() == []
    needed.need(a4)
    needed.need(a5)
    assert needed.resources() == [a1, a4, a2, a3, a5]

def test_convenience_clear():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    z1 = Resource(foo, 'd.js')
    z2 = Resource(foo, 'e.js', depends=[z1, x1])

    needed = init_needed()

    y1.need()
    assert needed.resources() == [x2, x1, y1]
    # For some reason,for example an error page needs to be rendered,
    # the currently needed resources need to be cleared.
    clear_needed()
    assert needed.resources() == []
    z2.need()
    assert needed.resources() == [z1, x1, z2]

def test_normalize_resource():
    foo = Library('foo', '')
    assert isinstance(normalize_resource(foo, 'f.css'), Resource)
    r1 = Resource(foo, 'f.js')
    assert normalize_resource(foo, r1) == r1

# XXX tests for hashed resources when this is enabled. Needs some plausible
# directory to test for hashes

# XXX better error reporting if unknown extensions are used


