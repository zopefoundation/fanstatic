import py

from fanstatic import (Library, ResourceInclusion, NeededInclusions,
                       GroupInclusion, NoNeededInclusions,
                       library_registry,
                       init_current_needed_inclusions,
                       get_current_needed_inclusions,
                       inclusion_renderers,
                       sort_inclusions_topological,
                       UnknownResourceExtension, EXTENSIONS)

def test_library_registry():
    assert library_registry.keys() == []
    with py.test.raises(KeyError) as e:
        library_registry['bar']

    foo = Library('foo', '')
    library_registry.add(foo)
    assert library_registry['foo'] is foo
    assert library_registry.keys() == ['foo']

    baz = Library('baz', '')
    library_registry[baz.name] = baz
    assert library_registry['baz'] is baz
    assert sorted(library_registry.keys()) == ['baz', 'foo']

def test_inclusion():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    needed = NeededInclusions()
    needed.need(y1)

    assert needed.inclusions() == [x2, x1, y1]

def test_group_inclusion():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])
    group = GroupInclusion([x1, x2])

    needed = NeededInclusions()
    needed.need(group)

    assert group.inclusions() == [x1, x2]

    more_stuff = ResourceInclusion(foo, 'more_stuff.js', depends=[group])
    assert more_stuff.inclusions() == [x1, x2, more_stuff]

def test_convenience_need_not_initialized():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    with py.test.raises(NoNeededInclusions):
        y1.need()
    with py.test.raises(NoNeededInclusions):
        get_current_needed_inclusions()

def test_convenience_need():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    needed = init_current_needed_inclusions()
    assert get_current_needed_inclusions() == needed
    assert get_current_needed_inclusions().inclusions() == []

    y1.need()

    assert get_current_needed_inclusions().inclusions() == [x2, x1, y1]

def test_redundant_inclusion():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    needed = NeededInclusions()

    needed.need(y1)
    needed.need(y1)
    assert needed.inclusions() == [x2, x1, y1]

    needed.need(x1)
    assert needed.inclusions() == [x2, x1, y1]

    needed.need(x2)
    assert needed.inclusions() == [x2, x1, y1]

def test_redundant_inclusion_reorder():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    needed = NeededInclusions()
    needed.need(x1)
    needed.need(x2)
    needed.need(y1)
    assert needed.inclusions() == [x2, x1, y1]

def test_redundant_more_complicated():
    foo = Library('foo', '')
    a1 = ResourceInclusion(foo, 'a1.js')
    a2 = ResourceInclusion(foo, 'a2.js', depends=[a1])
    a3 = ResourceInclusion(foo, 'a3.js', depends=[a2])
    a4 = ResourceInclusion(foo, 'a4.js', depends=[a1])

    needed = NeededInclusions()
    needed.need(a3)
    assert needed.inclusions() == [a1, a2, a3]
    needed.need(a4)
    assert needed.inclusions() == [a1, a2, a3, a4]

def test_redundant_more_complicated_reversed():
    foo = Library('foo', '')
    a1 = ResourceInclusion(foo, 'a1.js')
    a2 = ResourceInclusion(foo, 'a2.js', depends=[a1])
    a3 = ResourceInclusion(foo, 'a3.js', depends=[a2])
    a4 = ResourceInclusion(foo, 'a4.js', depends=[a1])

    needed = NeededInclusions()
    needed.need(a4)
    needed.need(a3)

    assert needed.inclusions() == [a1, a4, a2, a3]

def test_redundant_more_complicated_depends_on_all():
    foo = Library('foo', '')
    a1 = ResourceInclusion(foo, 'a1.js')
    a2 = ResourceInclusion(foo, 'a2.js', depends=[a1])
    a3 = ResourceInclusion(foo, 'a3.js', depends=[a2])
    a4 = ResourceInclusion(foo, 'a4.js', depends=[a1])
    a5 = ResourceInclusion(foo, 'a5.js', depends=[a4, a3])

    needed = NeededInclusions()
    needed.need(a5)

    assert needed.inclusions() == [a1, a4, a2, a3, a5]

def test_redundant_more_complicated_depends_on_all_reorder():
    foo = Library('foo', '')
    a1 = ResourceInclusion(foo, 'a1.js')
    a2 = ResourceInclusion(foo, 'a2.js', depends=[a1])
    a3 = ResourceInclusion(foo, 'a3.js', depends=[a2])
    a4 = ResourceInclusion(foo, 'a4.js', depends=[a1])
    a5 = ResourceInclusion(foo, 'a5.js', depends=[a4, a3])

    needed = NeededInclusions()
    needed.need(a3)
    needed.need(a5)

    assert needed.inclusions() == [a1, a2, a3, a4, a5]

def test_mode_fully_specified():
    foo = Library('foo', '')
    k_debug = ResourceInclusion(foo, 'k-debug.js')
    k = ResourceInclusion(foo, 'k.js', debug=k_debug)

    needed = NeededInclusions()
    needed.need(k)

    assert needed.inclusions() == [k]

    needed = NeededInclusions(mode='debug')
    needed.need(k)

    assert needed.inclusions() == [k_debug]

    needed = NeededInclusions

def test_mode_shortcut():
    foo = Library('foo', '')
    k = ResourceInclusion(foo, 'k.js', debug='k-debug.js')

    needed = NeededInclusions()
    needed.need(k)

    assert needed.inclusions() == [k]

    needed = NeededInclusions(mode='debug')
    needed.need(k)

    assert len(needed.inclusions()) == 1
    assert needed.inclusions()[0].relpath == 'k-debug.js'

def test_mode_unknown_default():
    foo = Library('foo', '')
    k_debug = ResourceInclusion(foo, 'k-debug.js')
    k = ResourceInclusion(foo, 'k.js', debug=k_debug)

    needed = NeededInclusions(mode='default')
    needed.need(k)

    assert needed.inclusions() == [k]

def test_rollup():
    foo = Library('foo', '')
    b1 = ResourceInclusion(foo, 'b1.js')
    b2 = ResourceInclusion(foo, 'b2.js')
    giant = ResourceInclusion(foo, 'giant.js', supersedes=[b1, b2])

    needed = NeededInclusions(rollup=True)
    needed.need(b1)
    needed.need(b2)

    assert needed.inclusions() == [giant]

def test_rollup_cannot():
    foo = Library('foo', '')
    b1 = ResourceInclusion(foo, 'b1.js')
    b2 = ResourceInclusion(foo, 'b2.js')

    giant = ResourceInclusion(foo, 'giant.js', supersedes=[b1, b2])

    needed = NeededInclusions(rollup=True)
    needed.need(b1)
    assert needed.inclusions() == [b1]

def test_rollup_larger():
    foo = Library('foo', '')
    c1 = ResourceInclusion(foo, 'c1.css')
    c2 = ResourceInclusion(foo, 'c2.css')
    c3 = ResourceInclusion(foo, 'c3.css')
    giant = ResourceInclusion(foo, 'giant.css', supersedes=[c1, c2, c3])

    needed = NeededInclusions(rollup=True)
    needed.need(c1)

    assert needed.inclusions() == [c1]

    needed.need(c2)

    assert needed.inclusions() == [c1, c2]

    needed.need(c3)

    assert needed.inclusions() == [giant]

def test_rollup_eager():
    foo = Library('foo', '')
    d1 = ResourceInclusion(foo, 'd1.js')
    d2 = ResourceInclusion(foo, 'd2.js')
    d3 = ResourceInclusion(foo, 'd3.js')
    giant = ResourceInclusion(foo, 'giant.js', supersedes=[d1, d2, d3],
                              eager_superseder=True)

    needed = NeededInclusions(rollup=True)
    needed.need(d1)
    assert needed.inclusions() == [giant]

    needed = NeededInclusions(rollup=True)
    needed.need(d1)
    needed.need(d2)
    assert needed.inclusions() == [giant]

def test_rollup_eager_competing():
    foo = Library('foo', '')
    d1 = ResourceInclusion(foo, 'd1.js')
    d2 = ResourceInclusion(foo, 'd2.js')
    d3 = ResourceInclusion(foo, 'd3.js')
    d4 = ResourceInclusion(foo, 'd4.js')
    giant = ResourceInclusion(foo, 'giant.js', supersedes=[d1, d2, d3],
                              eager_superseder=True)
    giant_bigger = ResourceInclusion(foo, 'giant-bigger.js',
                                     supersedes=[d1, d2, d3, d4],
                                     eager_superseder=True)

    needed = NeededInclusions(rollup=True)
    needed.need(d1)
    assert needed.inclusions() == [giant_bigger]

def test_rollup_eager_noneager_competing():
    foo = Library('foo', '')
    d1 = ResourceInclusion(foo, 'd1.js')
    d2 = ResourceInclusion(foo, 'd2.js')
    d3 = ResourceInclusion(foo, 'd3.js')
    giant = ResourceInclusion(foo, 'giant.js', supersedes=[d1, d2, d3],
                              eager_superseder=True)
    giant_noneager = ResourceInclusion(foo, 'giant-noneager.js',
                                       supersedes=[d1, d2, d3])
    needed = NeededInclusions(rollup=True)
    needed.need(d1)
    assert needed.inclusions() == [giant]

def test_rollup_size_competing():
    foo = Library('foo', '')
    d1 = ResourceInclusion(foo, 'd1.js')
    d2 = ResourceInclusion(foo, 'd2.js')
    d3 = ResourceInclusion(foo, 'd3.js')
    giant = ResourceInclusion(foo, 'giant.js', supersedes=[d1, d2])
    giant_bigger = ResourceInclusion(foo, 'giant-bigger.js',
                                     supersedes=[d1, d2, d3])

    needed = NeededInclusions(rollup=True)
    needed.need(d1)
    needed.need(d2)
    needed.need(d3)
    assert needed.inclusions() == [giant_bigger]

def test_rollup_eager_noneager_size_competing():
    foo = Library('foo', '')
    d1 = ResourceInclusion(foo, 'd1.js')
    d2 = ResourceInclusion(foo, 'd2.js')
    d3 = ResourceInclusion(foo, 'd3.js')
    d4 = ResourceInclusion(foo, 'd4.js')
    giant = ResourceInclusion(foo, 'giant.js', supersedes=[d1, d2, d3],
                              eager_superseder=True)
    giant_noneager_bigger = ResourceInclusion(foo, 'giant-noneager.js',
                                              supersedes=[d1, d2, d3, d4])
    needed = NeededInclusions(rollup=True)
    needed.need(d1)
    assert needed.inclusions() == [giant]

def test_rollup_modes():
    foo = Library('foo', '')
    f1 = ResourceInclusion(foo, 'f1.js', debug='f1-debug.js')
    f2 = ResourceInclusion(foo, 'f2.js', debug='f2-debug.js')
    giantf = ResourceInclusion(foo, 'giantf.js', supersedes=[f1, f2],
                               debug='giantf-debug.js')

    needed = NeededInclusions(rollup=True)
    needed.need(f1)
    needed.need(f2)
    assert needed.inclusions() == [giantf]

    needed = NeededInclusions(rollup=True, mode='debug')
    needed.need(f1)
    needed.need(f2)
    assert len(needed.inclusions()) == 1
    assert needed.inclusions()[0].relpath == 'giantf-debug.js'

def test_rollup_meaningless_rollup_mode():
    foo = Library('foo', '')
    g1 = ResourceInclusion(foo, 'g1.js')
    g2 = ResourceInclusion(foo, 'g2.js')
    giantg = ResourceInclusion(foo, 'giantg.js', supersedes=[g1, g2],
                               debug='giantg-debug.js')
    needed = NeededInclusions(rollup=True)
    needed.need(g1)
    needed.need(g2)
    assert needed.inclusions() == [giantg]

    needed = NeededInclusions(rollup=True, mode='debug')
    needed.need(g1)
    needed.need(g2)
    assert needed.inclusions() == [giantg]

def test_rollup_without_mode():
    foo = Library('foo', '')
    h1 = ResourceInclusion(foo, 'h1.js', debug='h1-debug.js')
    h2 = ResourceInclusion(foo, 'h2.js', debug='h2-debug.js')
    gianth = ResourceInclusion(foo, 'gianth.js', supersedes=[h1, h2])

    needed = NeededInclusions(rollup=True)
    needed.need(h1)
    needed.need(h2)
    assert needed.inclusions() == [gianth]

    needed = NeededInclusions(rollup=True, mode='debug')
    needed.need(h1)
    needed.need(h2)
    # no mode available for rollup
    assert len(needed.inclusions()) == 2
    assert needed.inclusions()[0].relpath == 'h1-debug.js'
    assert needed.inclusions()[1].relpath == 'h2-debug.js'

def test_rendering():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    needed = NeededInclusions()
    needed.need(y1)

    assert needed.render() == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''

def test_rendering_base_url():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    needed = NeededInclusions(base_url='http://localhost/static')
    needed.need(y1)

    assert needed.render() == '''\
<link rel="stylesheet" type="text/css" href="http://localhost/static/fanstatic/foo/b.css" />
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/c.js"></script>'''

def test_empty_base_url_and_publisher_signature():
    ''' When the base_url and publisher_signature are both empty strings,
    render a URL without them. '''
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    needed = NeededInclusions(base_url='', publisher_signature='')
    needed.need(x1)

    assert needed.render() == '''\
<script type="text/javascript" src="/foo/a.js"></script>'''

def test_rendering_base_url_assign():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    needed = NeededInclusions()
    needed.need(y1)

    needed.base_url = 'http://localhost/static'

    assert needed.render() == '''\
<link rel="stylesheet" type="text/css" href="http://localhost/static/fanstatic/foo/b.css" />
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/c.js"></script>'''

def test_rendering_publisher_signature():
    foo = Library('foo', '')

    needed = NeededInclusions(publisher_signature='waku')

    assert needed.library_url(foo) == '/waku/foo'

def test_html_insert():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    needed = NeededInclusions()
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
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    needed = NeededInclusions()
    needed.need(y1)

    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''
    assert bottom == ''

def test_html_top_bottom_set_bottom():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    needed = NeededInclusions(bottom=True)
    needed.need(y1)

    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''
    assert bottom == ''

def test_html_top_bottom_force_bottom():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    needed = NeededInclusions(bottom=True, force_bottom=True)
    needed.need(y1)

    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />'''
    assert bottom == '''\
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''


def test_html_bottom_safe():
    foo = Library('foo', '')
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])
    y2 = ResourceInclusion(foo, 'y2.js', bottom=True)

    needed = NeededInclusions()
    needed.need(y1)
    needed.need(y2)
    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>
<script type="text/javascript" src="/fanstatic/foo/y2.js"></script>'''
    assert bottom == ''

    needed = NeededInclusions(bottom=True)
    needed.need(y1)
    needed.need(y2)
    top, bottom = needed.render_topbottom()
    assert top == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''
    assert bottom == '''\
<script type="text/javascript" src="/fanstatic/foo/y2.js"></script>'''

    needed = NeededInclusions(bottom=True, force_bottom=True)
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
    x1 = ResourceInclusion(foo, 'a.js')
    x2 = ResourceInclusion(foo, 'b.css')
    y1 = ResourceInclusion(foo, 'c.js', depends=[x1, x2])

    html = "<html><head>rest of head</head><body>rest of body</body></html>"

    needed = NeededInclusions(bottom=True, force_bottom=True)
    needed.need(y1)
    assert needed.render_topbottom_into_html(html) == '''\
<html><head>
    <link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
rest of head</head><body>rest of body<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script></body></html>'''

def test_sorting_inclusions():
    foo = Library('foo', '')

    a1 = ResourceInclusion(foo, 'a1.js')
    a2 = ResourceInclusion(foo, 'a2.js', depends=[a1])
    a3 = ResourceInclusion(foo, 'a3.js', depends=[a2])
    a4 = ResourceInclusion(foo, 'a4.js', depends=[a1])
    a5 = ResourceInclusion(foo, 'a5.js', depends=[a4, a3])

    assert sort_inclusions_topological([a5, a3, a1, a2, a4]) == [
        a1, a4, a2, a3, a5]

def test_inclusion_renderers():
    assert sorted(inclusion_renderers.keys()) == ['.css', '.js', '.kss']

    assert inclusion_renderers['.js']('http://localhost/script.js') == (
         '<script type="text/javascript" src="http://localhost/script.js"></script>')


# XXX whole EXTENSIONS business is weird
def test_add_inclusion_renderer():
    foo = Library('foo', '')
    a = ResourceInclusion(foo, 'nothing.unknown')
    # XXX hack
    EXTENSIONS.append('.unknown')

    needed = NeededInclusions()
    needed.need(a)
    with py.test.raises(UnknownResourceExtension):
        needed.render()

    def render_unknown(url):
        return '<link rel="unknown" href="%s" />' % url

    inclusion_renderers['.unknown'] = render_unknown
    assert needed.render() == ('<link rel="unknown" href="/fanstatic/foo/nothing.unknown" />')


# XXX tests for hashed resources when this is enabled. Needs some plausible
# directory to test for hashes

# XXX better error reporting if unknown extensions are used

# XXX test for library defined in full package; do we really want to
# depend on buildout and incur the performance penalty or shall we
# simply ignore this issue?


