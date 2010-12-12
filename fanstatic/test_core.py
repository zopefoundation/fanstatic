import pytest

from fanstatic import (Library, Resource, NeededResources,
                       GroupResource, NoNeededResources,
                       init_needed,
                       get_needed,
                       inclusion_renderers,
                       sort_resources_topological,
                       UnknownResourceExtension, EXTENSIONS)


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

    with pytest.raises(NoNeededResources):
        y1.need()
    with pytest.raises(NoNeededResources):
        get_needed()

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

    needed = NeededResources(mode='debug')
    needed.need(k)

    assert needed.resources() == [k_debug]

    needed = NeededResources

def test_mode_shortcut():
    foo = Library('foo', '')
    k = Resource(foo, 'k.js', debug='k-debug.js')

    needed = NeededResources()
    needed.need(k)

    assert needed.resources() == [k]

    needed = NeededResources(mode='debug')
    needed.need(k)

    assert len(needed.resources()) == 1
    assert needed.resources()[0].relpath == 'k-debug.js'

def test_mode_unknown_default():
    foo = Library('foo', '')
    k_debug = Resource(foo, 'k-debug.js')
    k = Resource(foo, 'k.js', debug=k_debug)

    needed = NeededResources(mode='default')
    needed.need(k)

    assert needed.resources() == [k]

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

    needed = NeededResources(rollup=True, mode='debug')
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

    needed = NeededResources(rollup=True, mode='debug')
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

    needed = NeededResources(rollup=True, mode='debug')
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

    needed = NeededResources()
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

    needed = NeededResources()

    assert needed.library_url(foo) == '/fanstatic/foo'

def test_library_url_publisher_signature():
    foo = Library('foo', '')

    needed = NeededResources(publisher_signature='waku')

    assert needed.library_url(foo) == '/waku/foo'

def test_library_url_base_url():
    foo = Library('foo', '')

    needed = NeededResources(base_url="http://example.com/something")

    assert (needed.library_url(foo) ==
            'http://example.com/something/fanstatic/foo')

def test_library_url_hashing(tmpdir):
    foo = Library('foo', tmpdir.strpath)

    needed = NeededResources(hashing=True)

    assert (needed.library_url(foo) ==
            '/fanstatic/foo/:hash:d41d8cd98f00b204e9800998ecf8427e')

def test_library_url_hashing_nodevmode(tmpdir):
    foo = Library('foo', tmpdir.strpath)

    needed = NeededResources(hashing=True)

    url = needed.library_url(foo)

    # now create a file
    resource = tmpdir.join('test.js')
    resource.write('/* test */')

    # since we're not in devmode, the hash in the URL won't change
    assert needed.library_url(foo) == url

def test_library_url_hashing_devmode(tmpdir):
    foo = Library('foo', tmpdir.strpath)

    needed = NeededResources(hashing=True, devmode=True)

    url = needed.library_url(foo)

    # now create a file
    resource = tmpdir.join('test.js')
    resource.write('/* test */')

    # in devmode the hash is recalculated now, so it changes
    assert needed.library_url(foo) != url

def test_html_insert():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = NeededResources()
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

    needed = NeededResources()
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

    needed = NeededResources(bottom=True)
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

    needed = NeededResources(bottom=True, force_bottom=True)
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

    needed = NeededResources()
    needed.need(y1)
    needed.need(y2)
    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>
<script type="text/javascript" src="/fanstatic/foo/y2.js"></script>'''
    assert bottom == ''

    needed = NeededResources(bottom=True)
    needed.need(y1)
    needed.need(y2)
    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''
    assert bottom == '''\
<script type="text/javascript" src="/fanstatic/foo/y2.js"></script>'''

    needed = NeededResources(bottom=True, force_bottom=True)
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

    needed = NeededResources(bottom=True, force_bottom=True)
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
    assert sorted(inclusion_renderers.keys()) == ['.css', '.js']

    assert inclusion_renderers['.js']('http://localhost/script.js') == (
         '<script type="text/javascript" src="http://localhost/script.js"></script>')


# XXX whole EXTENSIONS business is weird
def test_add_inclusion_renderer():
    foo = Library('foo', '')
    a = Resource(foo, 'nothing.unknown')
    # XXX hack
    EXTENSIONS.append('.unknown')

    needed = NeededResources()
    needed.need(a)
    with pytest.raises(UnknownResourceExtension):
        needed.render()

    def render_unknown(url):
        return '<link rel="unknown" href="%s" />' % url

    inclusion_renderers['.unknown'] = render_unknown
    assert needed.render() == ('<link rel="unknown" href="/fanstatic/foo/nothing.unknown" />')


# XXX tests for hashed resources when this is enabled. Needs some plausible
# directory to test for hashes

# XXX better error reporting if unknown extensions are used


