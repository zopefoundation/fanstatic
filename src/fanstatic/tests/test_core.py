import os
import re
import time

import pytest

from fanstatic import NEEDED
from fanstatic import ConfigurationError
from fanstatic import Group
from fanstatic import Inclusion
from fanstatic import Library
from fanstatic import LibraryDependencyCycleError
from fanstatic import NeededResources
from fanstatic import Resource
from fanstatic import UnknownResourceError
from fanstatic import UnknownResourceExtensionError
from fanstatic import clear_needed
from fanstatic import del_needed
from fanstatic import get_needed
from fanstatic import init_needed
from fanstatic import register_inclusion_renderer
from fanstatic import set_resource_file_existence_checking
from fanstatic.core import ModeResourceDependencyError
from fanstatic.core import inclusion_renderers
from fanstatic.core import thread_local_needed_data
from fanstatic.inclusion import bundle_resources
from fanstatic.inclusion import rollup_resources
from fanstatic.inclusion import sort_resources


def test_resource():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = init_needed()
    needed.need(y1)

    assert needed.resources() == {x2, x1, y1}


def test_resource_file_exists(tmpdir):
    tmpdir.join('a.js').write('/* hello world */')
    # by default this is set to False during the tests, but in normal
    # non-test circumstances this is set to True, and we want to
    # test things for real here
    set_resource_file_existence_checking(True)
    foo = Library('foo', tmpdir.strpath)
    # since a.js exists, this should work
    Resource(foo, 'a.js')
    # now we try to create a resource that refers to a file
    # that doesn't exist
    with pytest.raises(UnknownResourceError):
        Resource(foo, 'b.js')

    tmpdir.mkdir('sub').join('c.css').write('c')
    Resource(foo, 'sub/c.css')


def test_resource_register_with_library():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js', minified='a.min.js')

    assert len(foo.known_resources) == 2
    assert x1 in foo.known_resources.values()

    # Can not use the same relpath for two Resource declarations.
    with pytest.raises(ConfigurationError):
        Resource(foo, 'a.js')


def test_group_resource():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    group = Group([x1, x2])

    needed = init_needed()
    needed.need(group)

    assert group.resources == {x1, x2}

    more_stuff = Resource(foo, 'more_stuff.js', depends=[group])
    assert more_stuff.resources == {x1, x2, more_stuff}


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

    # A dummy never has resources:
    assert not dummy.has_resources()

    dummy.need(y1)
    with pytest.raises(NotImplementedError):
        dummy.resources()


def test_convenience_clear_not_initialized():
    # This test is put near the top of this module, or at least before
    # the very first time ``init_needed()`` is called.
    dummy = get_needed()
    with pytest.raises(NotImplementedError):
        dummy.clear()
    with pytest.raises(NotImplementedError):
        clear_needed()

    # Initialize a needed resources object.
    needed = init_needed()
    assert get_needed() == needed
    assert thread_local_needed_data.__dict__[NEEDED] == needed

    # Clear it.
    del_needed()

    # It is gone, really.
    with pytest.raises(KeyError):
        thread_local_needed_data.__dict__[NEEDED]

    # Clearing it again is OK.
    del_needed()

    # get_needed still work, dummy-style.
    dummy2 = get_needed()
    assert dummy2 != needed
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
    assert get_needed().resources() == set()

    y1.need()

    assert get_needed().resources() == {x2, x1, y1}


def test_convenience_group_resource_need():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js')
    group = Group([x1, x2, y1])

    needed = init_needed()
    assert get_needed() == needed
    assert get_needed().resources() == set()

    group.need()

    assert get_needed().resources() == {x2, x1, y1}


def test_add_dependency_resource_to_resource():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    b1 = Resource(foo, 'b1.js', depends=[a1])
    c1 = Resource(foo, 'c1.js', depends=[b1])

    assert a1.depends == set()
    assert a1.resources == {a1}

    assert b1.depends == {a1}
    assert b1.resources == {a1, b1}

    assert c1.depends == {b1}
    assert c1.resources == {a1, b1, c1}

    a2 = Resource(foo, 'a2.js')
    b1.add_dependency(a2)

    assert b1.depends == {a1, a2}
    assert b1.resources == {a1, a2, b1}

    assert c1.depends == {b1}
    assert c1.resources == {a1, a2, b1, c1}

    # Adding it twice does not change anything.
    b1.add_dependency(a2)

    assert b1.depends == {a1, a2}
    assert b1.resources == {a1, a2, b1}

    assert c1.depends == {b1}
    assert c1.resources == {a1, a2, b1, c1}


def test_cannot_add_dependency_loop():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    b1 = Resource(foo, 'b1.js', depends=[a1])

    with pytest.raises(ValueError):
        a1.add_dependency(b1)


def test_add_dependency_group_to_resource():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    b1 = Resource(foo, 'b1.js', depends=[a1])
    c1 = Resource(foo, 'c1.js', depends=[b1])

    assert a1.depends == set()
    assert a1.resources == {a1}

    assert b1.depends == {a1}
    assert b1.resources == {a1, b1}

    assert c1.depends == {b1}
    assert c1.resources == {a1, b1, c1}

    a2 = Resource(foo, 'a2.js')
    a3 = Group([a1, a2])
    b1.add_dependency(a3)

    assert b1.depends == {a1, a3}
    assert b1.resources == {a1, a2, b1}

    assert c1.depends == {b1}
    assert c1.resources == {a1, a2, b1, c1}

    # Adding it twice does not change anything.
    b1.add_dependency(a3)

    assert b1.depends == {a1, a3}
    assert b1.resources == {a1, a2, b1}

    assert c1.depends == {b1}
    assert c1.resources == {a1, a2, b1, c1}


def test_add_dependency_resource_to_group():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    b1 = Group([a1])
    c1 = Resource(foo, 'c1.js', depends=[b1])

    assert a1.depends == set()
    assert a1.resources == {a1}

    assert b1.depends == {a1}
    assert b1.resources == {a1}

    assert c1.depends == {b1}
    assert c1.resources == {a1, c1}

    a2 = Resource(foo, 'a2.js')
    b1.add_dependency(a2)

    assert b1.depends == {a1, a2}
    assert b1.resources == {a1, a2}

    assert c1.depends == {b1}
    assert c1.resources == {a1, a2, c1}

    # Adding it twice does not change anything.
    b1.add_dependency(a2)

    assert b1.depends == {a1, a2}
    assert b1.resources == {a1, a2}

    assert c1.depends == {b1}
    assert c1.resources == {a1, a2, c1}


def test_dependables():
    foo = Library('foo', '')
    a = Resource(foo, 'a.js')
    b = Resource(foo, 'b.js')
    g1 = Group([a, b])
    c = Resource(foo, 'c.js', depends=[g1])
    g2 = Group([g1])
    g3 = Group([g1, g2])

    assert a.supports == {g1}
    assert a.list_assets() == {a}
    assert a.list_supporting() == {c, g1, g2, g3}

    assert b.supports == {g1}
    assert b.list_assets() == {b}
    assert b.list_supporting() == {c, g1, g2, g3}

    assert c.depends == {g1}
    assert c.resources == {a, b, c}
    assert c.list_assets() == {c}
    assert c.list_supporting() == set()

    assert g1.depends == {a, b}
    assert g1.resources == {a, b}
    assert g1.supports == {c, g2, g3}
    assert g1.list_assets() == {a, b}
    assert g1.list_supporting() == {c, g2, g3}

    assert g2.depends == {g1}
    assert g2.resources == {a, b}
    assert g2.supports == {g3}
    assert g2.list_assets() == {a, b}
    assert g2.list_supporting() == {g3}

    assert g3.depends == {g1, g2}
    assert g3.resources == {a, b}
    assert g3.list_assets() == {a, b}
    assert g3.list_supporting() == set()

    needed = init_needed()
    needed.need(c)
    assert needed.resources() == {a, b, c}


def test_redundant_resource():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = init_needed()

    needed.need(y1)
    needed.need(y1)
    incl = Inclusion(needed)
    assert incl.resources == [x2, x1, y1]

    needed.need(x1)
    incl = Inclusion(needed)
    assert incl.resources == [x2, x1, y1]

    needed.need(x2)
    incl = Inclusion(needed)
    assert incl.resources == [x2, x1, y1]


def test_redundant_resource_reorder():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = init_needed()
    needed.need(x1)
    needed.need(x2)
    needed.need(y1)
    incl = Inclusion(needed)
    assert incl.resources == [x2, x1, y1]


def test_redundant_more_complicated():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    a2 = Resource(foo, 'a2.js', depends=[a1])
    a3 = Resource(foo, 'a3.js', depends=[a2])
    a4 = Resource(foo, 'a4.js', depends=[a1])

    needed = init_needed()
    needed.need(a3)

    incl = Inclusion(needed)
    assert incl.resources == [a1, a2, a3]
    needed.need(a4)
    # a4 is sorted before a3, because it is less deep
    # in the dependency tree
    incl = Inclusion(needed)
    assert incl.resources == [a1, a2, a4, a3]


def test_redundant_more_complicated_reversed():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    a2 = Resource(foo, 'a2.js', depends=[a1])
    a3 = Resource(foo, 'a3.js', depends=[a2])
    a4 = Resource(foo, 'a4.js', depends=[a1])

    needed = init_needed()
    needed.need(a4)
    needed.need(a3)
    # this will always be consistent, no matter
    # in what order we need the resources
    incl = Inclusion(needed)
    assert incl.resources == [a1, a2, a4, a3]


def test_redundant_more_complicated_depends_on_all():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    a2 = Resource(foo, 'a2.js', depends=[a1])
    a3 = Resource(foo, 'a3.js', depends=[a2])
    a4 = Resource(foo, 'a4.js', depends=[a1])
    a5 = Resource(foo, 'a5.js', depends=[a4, a3])

    needed = init_needed()
    needed.need(a5)
    incl = Inclusion(needed)
    assert incl.resources == [a1, a2, a4, a3, a5]


def test_redundant_more_complicated_depends_on_all_reorder():
    foo = Library('foo', '')
    a1 = Resource(foo, 'a1.js')
    a2 = Resource(foo, 'a2.js', depends=[a1])
    a3 = Resource(foo, 'a3.js', depends=[a2])
    a4 = Resource(foo, 'a4.js', depends=[a1])
    a5 = Resource(foo, 'a5.js', depends=[a4, a3])

    needed = init_needed()
    needed.need(a3)
    needed.need(a5)
    incl = Inclusion(needed)
    assert incl.resources == [a1, a2, a4, a3, a5]


def test_mode_fully_specified():
    foo = Library('foo', '')
    k_debug = Resource(foo, 'k-debug.js')
    k = Resource(foo, 'k.js', debug=k_debug)
    x = Resource(foo, 'x.js', minified='x-min.js')

    needed = init_needed()
    needed.need(k)
    incl = Inclusion(needed)
    assert incl.resources == [k]

    incl = Inclusion(needed, mode='debug')
    assert incl.resources == [k_debug]

    # If no minified can be found, the 'raw' resource is taken.
    incl = Inclusion(needed, mode='minified')
    assert incl.resources == [k]

    # If only a minified resource is defined, debug returns the raw version.
    needed = init_needed()
    needed.need(x)

    incl = Inclusion(needed, mode='debug')
    assert incl.resources == [x]
    incl = Inclusion(needed, mode='minified')
    assert incl.resources == [x.modes['minified']]


def test_mode_shortcut_inherit_parameters():
    def special_renderer(url):
        return '<special href="%s"/>' % url

    foo = Library('foo', '')
    a = Resource(foo, 'a.js')
    k = Resource(
        foo, 'k.js', debug='k-debug.js',
        depends=[a],
        dont_bundle=True,
        renderer=special_renderer)
    debug_resource = k.modes['debug']
    assert debug_resource.depends == k.depends
    assert debug_resource.renderer == special_renderer
    assert debug_resource.dont_bundle


def test_rollup():
    foo = Library('foo', '')
    b1 = Resource(foo, 'b1.js')
    b2 = Resource(foo, 'b2.js')
    giant = Resource(foo, 'giant.js', supersedes=[b1, b2])

    assert rollup_resources([b1, b2]) == {giant}


def test_rollup_cannot():
    foo = Library('foo', '')
    b1 = Resource(foo, 'b1.js')
    b2 = Resource(foo, 'b2.js')

    Resource(foo, 'giant.js', supersedes=[b1, b2])

    assert rollup_resources([b1]) == {b1}


def test_rollup_larger():
    foo = Library('foo', '')
    c1 = Resource(foo, 'c1.css')
    c2 = Resource(foo, 'c2.css')
    c3 = Resource(foo, 'c3.css')
    giant = Resource(foo, 'giant.css', supersedes=[c1, c2, c3])

    assert rollup_resources([c1]) == {c1}
    assert rollup_resources([c1, c2]) == {c1, c2}
    assert rollup_resources([c1, c2, c3]) == {giant}


def test_rollup_size_competing():
    foo = Library('foo', '')
    d1 = Resource(foo, 'd1.js')
    d2 = Resource(foo, 'd2.js')
    d3 = Resource(foo, 'd3.js')
    Resource(foo, 'giant.js', supersedes=[d1, d2])
    giant_bigger = Resource(foo, 'giant-bigger.js',
                            supersedes=[d1, d2, d3])

    assert rollup_resources([d1, d2, d3]) == {giant_bigger}


def test_rollup_with_slot():
    from fanstatic import Slot

    lib = Library('lib', '')
    c = Resource(lib, 'c.js')
    slot = Slot(lib, '.js', depends=[c])
    a = Resource(lib, 'a.js', depends=[slot])
    b = Resource(lib, 'b.js', depends=[c])

    needed = init_needed()
    needed.need(a, {slot: b})

    incl = Inclusion(needed, rollup=True)
    assert len(incl.resources) == 3
    assert a in incl.resources
    assert c in incl.resources


def test_inclusion_rollup_and_debug():
    foo = Library('foo', '')
    f1 = Resource(foo, 'f1.js', debug='f1-debug.js')
    f2 = Resource(foo, 'f2.js', debug='f2-debug.js')
    giantf = Resource(foo, 'giantf.js', supersedes=[f1, f2],
                      debug='giantf-debug.js')

    needed = init_needed(resources=[f1, f2])
    incl = Inclusion(needed, rollup=True)
    assert incl.resources == [giantf]

    incl = Inclusion(needed, rollup=True, mode='debug')
    assert incl.resources == [giantf.modes['debug']]


def test_inclusion_rollup_and_debug_missing():
    foo = Library('foo', '')
    h1 = Resource(foo, 'h1.js', debug='h1-debug.js')
    h2 = Resource(foo, 'h2.js', debug='h2-debug.js')
    gianth = Resource(foo, 'gianth.js', supersedes=[h1, h2])

    needed = init_needed(resources=[h1, h2])
    incl = Inclusion(needed, rollup=True, mode='debug')
    # No mode debug version of the rollup use it instead
    assert incl.resources == [gianth]


def test_rendering():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = init_needed(resources=[y1])
    incl = Inclusion(needed)

    assert incl.render() == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''


def test_rendering_base_url():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = init_needed(resources=[y1])
    incl = Inclusion(needed)
    assert incl.render() == '''\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" />
<script type="text/javascript" src="/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="/fanstatic/foo/c.js"></script>'''

    needed = init_needed(
        base_url='http://localhost/static', resources=[y1])
    incl = Inclusion(needed)
    assert incl.render() == '''\
<link rel="stylesheet" type="text/css" href="http://localhost/static/fanstatic/foo/b.css" />
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/c.js"></script>'''  # noqa: E501 line too long
    # The base_url has been set.
    assert needed.has_base_url()

    needed.set_base_url('foo')
    # The base_url can only be set once.
    assert needed._base_url == 'http://localhost/static'


def test_empty_base_url_and_publisher_signature():
    '''When the base_url is not set and the publisher_signature is an empty
    string, render a URL without them. '''
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    needed = init_needed(publisher_signature='', resources=[x1])
    incl = Inclusion(needed)
    assert incl.render() == '''\
<script type="text/javascript" src="/foo/a.js"></script>'''


def test_rendering_base_url_assign():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    needed = init_needed(resources=[y1])
    needed.set_base_url('http://localhost/static')
    incl = Inclusion(needed)
    assert incl.render() == '''\
<link rel="stylesheet" type="text/css" href="http://localhost/static/fanstatic/foo/b.css" />
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/a.js"></script>
<script type="text/javascript" src="http://localhost/static/fanstatic/foo/c.js"></script>'''  # noqa: E501 line too long


def test_library_url_default_publisher_signature():
    foo = Library('foo', '')

    needed = init_needed()

    assert needed.library_url(foo) == '/fanstatic/foo'


def test_library_url_publisher_signature():
    foo = Library('foo', '')

    needed = init_needed(publisher_signature='waku')

    assert needed.library_url(foo) == '/waku/foo'


def test_library_url_base_url():
    foo = Library('foo', '')

    needed = init_needed(base_url="http://example.com/something")

    assert (needed.library_url(foo) ==
            'http://example.com/something/fanstatic/foo')


def test_library_url_script_name():
    foo = Library('foo', '')
    needed = init_needed(script_name='/root')
    assert needed.library_url(foo) == '/root/fanstatic/foo'


def test_library_url_script_name_base_url():
    foo = Library('foo', '')
    needed = init_needed(
        script_name='/root', base_url="http://example.com/something")

    # base_url is set so script_name should be ignored
    assert (needed.library_url(foo) ==
            'http://example.com/something/fanstatic/foo')


def test_library_url_version_hashing(tmpdir):
    foo = Library('foo', tmpdir.strpath)
    # If the Library defines a version, the version is used.
    bar = Library('bar', '', version='1')

    needed = init_needed(versioning=True)
    url = needed.library_url(foo)
    assert re.match('/fanstatic/foo/:version:[0-9T:.-]*$', url)

    # The md5 based version URL is available through the
    # `versioning_use_md5` parameter:
    needed = init_needed(versioning=True, versioning_use_md5=True)
    md5_url = needed.library_url(foo)
    assert url != md5_url

    assert needed.library_url(bar) == '/fanstatic/bar/:version:1'


def test_library_url_hashing_norecompute(tmpdir):
    foo = Library('foo', tmpdir.strpath)

    needed = init_needed(versioning=True, recompute_hashes=False)

    url = needed.library_url(foo)

    # now create a file
    resource = tmpdir.join('test.js')
    resource.write('/* test */')

    # since we're not re-computing hashes, the hash in the URL won't change
    assert needed.library_url(foo) == url


def test_library_url_hashing_recompute(tmpdir):
    foo = Library('foo', tmpdir.strpath)

    needed = init_needed(versioning=True, recompute_hashes=True)

    url = needed.library_url(foo)

    # now create a file
    resource = tmpdir.join('test.js')

    time.sleep(0.5)
    # Sleep extra long on filesystems that report in seconds
    # instead of milliseconds.
    if os.path.getmtime(os.curdir).is_integer():
        time.sleep(1)
    resource.write('/* test */')

    # For a new request, the url is recomputed.
    new_needed = init_needed(versioning=True, recompute_hashes=True)
    # the hash is recalculated now, so it changes
    assert new_needed.library_url(foo) != url


def test_library_url_with_url_caching(tmpdir):
    foo = Library('foo', tmpdir.strpath)

    needed = init_needed(versioning=True, recompute_hashes=True)

    url = needed.library_url(foo)

    # now create a file
    resource = tmpdir.join('test.js')

    time.sleep(0.5)
    # Sleep extra long on filesystems that report in seconds
    # instead of milliseconds.
    if os.path.getmtime(os.curdir).is_integer():
        time.sleep(1)
    resource.write('/* test */')

    # The url is cached on the needed resources object.
    assert needed.library_url(foo) == url


# XXX add sanity checks: cannot declare something bottom safe while
# what it depends on isn't bottom safe


def test_inclusion_renderers():
    assert sorted(
        [(order, key)
         for key, (order, _) in inclusion_renderers.items()]
    ) == [(10, '.css'), (20, '.js'), (30, '.ico')]
    _, renderer = inclusion_renderers['.js']
    assert renderer('http://localhost/script.js') == (
        '<script type="text/javascript"'
        ' src="http://localhost/script.js"></script>')


def test_register_inclusion_renderer():
    foo = Library('foo', '')

    with pytest.raises(UnknownResourceExtensionError):
        # The renderer for '.unknown' is not yet defined.
        Resource(foo, 'nothing.unknown')

    def render_unknown(url):
        return '<link rel="unknown" href="%s" />' % url

    register_inclusion_renderer('.unknown', render_unknown)
    a = Resource(foo, 'stuff.unknown')

    needed = init_needed(resources=[a])
    incl = Inclusion(needed)
    assert incl.render() == \
        '<link rel="unknown" href="/fanstatic/foo/stuff.unknown" />'


def test_sort_registered_inclusion_renderers_in_order():
    from fanstatic import get_library_registry
    foo = Library('foo', '')

    def render_unknown(url):
        return '<unknown href="%s"/>' % url

    register_inclusion_renderer('.later', render_unknown, 50)
    register_inclusion_renderer('.sooner', render_unknown, 5)
    register_inclusion_renderer('.between', render_unknown, 25)
    a = Resource(foo, 'nothing.later')
    b = Resource(foo, 'something.js')
    c = Resource(foo, 'something.css')
    d = Resource(foo, 'something.ico')
    e = Resource(foo, 'nothing.sooner')
    f = Resource(foo, 'nothing.between')

    get_library_registry().prepare()
    assert sort_resources([a, b, c, d]) == [c, b, d, a]
    assert sort_resources([a, b, c, d, e]) == [e, c, b, d, a]
    assert sort_resources([a, b, c, d, e, f]) == [e, c, b, f, d, a]


def test_custom_renderer_for_resource():
    foo = Library('foo', '')
    from fanstatic.core import render_print_css

    def render_unknown(url):
        return '<unknown href="%s"/>' % url

    a = Resource(foo, 'printstylesheet.css', renderer=render_print_css)
    b = Resource(foo, 'nothing.unknown', renderer=render_unknown)
    needed = init_needed()
    needed.need(a)
    incl = Inclusion(needed)
    assert incl.render() == """\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/printstylesheet.css" media="print" />"""  # noqa: E501 line too long

    needed.need(b)
    incl = Inclusion(needed)
    assert incl.render() == """\
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/printstylesheet.css" media="print" />
<unknown href="/fanstatic/foo/nothing.unknown"/>"""  # noqa: E501 line too long


def test_custom_renderer_keep_together():
    foo = Library('foo', '')

    def render_print_css(url):
        return (
            '<link rel="stylesheet" type="text/css" href="%s" media="print"/>'
            % url)

    a = Resource(foo, 'printstylesheet.css', renderer=render_print_css)
    b = Resource(foo, 'regular.css')
    c = Resource(foo, 'something.js')

    needed = init_needed()
    needed.need(a)
    needed.need(b)
    needed.need(c)

    incl = Inclusion(needed)
    assert incl.resources == [a, b, c]


def test_resource_subclass_render():
    foo = Library('foo', '')

    class MyResource(Resource):
        def render(self, library_url):
            return '<myresource reference="{}/{}"/>'.format(
                library_url, self.relpath)

    a = MyResource(foo, 'printstylesheet.css')
    needed = init_needed(resources=[a])
    incl = Inclusion(needed)
    assert incl.render() == """\
<myresource reference="/fanstatic/foo/printstylesheet.css"/>"""


def test_clear():
    foo = Library('foo', '')

    a1 = Resource(foo, 'a1.js')
    a2 = Resource(foo, 'a2.js', depends=[a1])
    a3 = Resource(foo, 'a3.js', depends=[a2])

    a4 = Resource(foo, 'a4.js', depends=[a1])
    a5 = Resource(foo, 'a5.js', depends=[a4, a3])

    needed = init_needed(resources=[a1, a2, a3])
    assert needed.resources() == {a1, a2, a3}
    # For some reason,for example an error page needs to be rendered,
    # the currently needed resources need to be cleared.
    needed.clear()
    assert len(needed.resources()) == 0
    needed.need(a4)
    needed.need(a5)
    assert needed.resources() == {a1, a2, a4, a3, a5}


def test_convenience_clear():
    foo = Library('foo', '')
    x1 = Resource(foo, 'a.js')
    x2 = Resource(foo, 'b.css')
    y1 = Resource(foo, 'c.js', depends=[x1, x2])

    z1 = Resource(foo, 'd.js')
    z2 = Resource(foo, 'e.js', depends=[z1, x1])

    needed = init_needed(resources=[y1])

    assert sort_resources(needed.resources()) == [x2, x1, y1]
    # For some reason,for example an error page needs to be rendered,
    # the currently needed resources need to be cleared.
    clear_needed()
    assert len(needed.resources()) == 0
    z2.need()
    assert sort_resources(needed.resources()) == [x1, z1, z2]


def test_check_resource_dependencies():
    foo = Library('foo', '')

    r1 = Resource(foo, 'r1.css')
    r2 = Resource(foo, 'r2.css')
    r3 = Resource(foo, 'r3.css', depends=[r1, r2])
    # https://bitbucket.org/fanstatic/fanstatic/issue/63
    # If a resource is a mode (debug, minified) of a resource, its
    # dependencies should be the same or a subset of the dependencies that
    # this mode replaces.
    with pytest.raises(ModeResourceDependencyError):
        Resource(foo, 'r4.css', depends=[r1], minified=r3)


def test_normalize_string():
    foo = Library('foo', '')
    r1 = Resource(foo, 'r1.css', minified='r1.min.css')
    assert isinstance(r1.modes['minified'], Resource)


def test_sort_group_per_renderer():
    foo = Library('foo', '')
    a_js = Resource(foo, 'a.js')
    b_css = Resource(foo, 'b.css')
    c_js = Resource(foo, 'c.js')
    a1_js = Resource(foo, 'a1.js', depends=[b_css])

    needed = init_needed()
    needed.need(a_js)
    needed.need(b_css)
    needed.need(c_js)
    needed.need(a1_js)

    assert sort_resources(needed.resources()) == [b_css, a_js, c_js, a1_js]


def test_sort_group_per_library():
    foo = Library('foo', '')
    bar = Library('bar', '')

    e = Resource(foo, 'e.js')
    d = Resource(foo, 'd.js', depends=[e])
    c = Resource(bar, 'c.js', depends=[e])
    b = Resource(bar, 'b.js')
    a = Resource(bar, 'a.js', depends=[c])

    needed = init_needed()
    needed.need(a)
    needed.need(b)
    needed.need(c)
    needed.need(d)
    needed.need(e)

    assert sort_resources(needed.resources()) == [e, d, b, c, a]


def test_sort_library_by_name():
    b_lib = Library('b_lib', '')
    a_lib = Library('a_lib', '')

    a_a = Resource(a_lib, 'a.js')
    a_b = Resource(b_lib, 'a.js')

    needed = init_needed()
    needed.need(a_b)
    needed.need(a_a)

    assert sort_resources(needed.resources()) == [a_a, a_b]


def test_sort_resources_libraries_together():
    K = Library('K', '')
    L = Library('L', '')
    M = Library('M', '')
    N = Library('N', '')

    k1 = Resource(K, 'k1.js')
    l1 = Resource(L, 'l1.js')
    m1 = Resource(M, 'm1.js', depends=[k1])
    m2 = Resource(M, 'm2.js', depends=[l1])
    n1 = Resource(N, 'n1.js', depends=[m1])

    needed = init_needed()
    needed.need(m1)
    needed.need(m2)
    # sort_resources makes an efficient ordering, grouping m1 and m2 together
    # after their dependencies (they are in the same library)
    assert sort_resources(needed.resources()) == [k1, l1, m1, m2]

    needed = init_needed()
    needed.need(n1)
    needed.need(m2)
    # the order is unaffected by the ordering of inclusions
    assert sort_resources(needed.resources()) == [k1, l1, m1, m2, n1]


def test_sort_resources_library_sorting():
    # a complicated example that makes sure libraries are sorted
    # correctly to obey ordering constraints but still groups them
    X = Library('X', '')
    Y = Library('Y', '')
    Z = Library('Z', '')

    a = Resource(X, 'a.js')
    b = Resource(Z, 'b.js', depends=[a])

    c = Resource(Y, 'c.js')
    c1 = Resource(Y, 'c1.js', depends=[c])
    c2 = Resource(Y, 'c2.js', depends=[c1])
    d = Resource(Z, 'd.js', depends=[c])
    e = Resource(Z, 'e.js')

    needed = init_needed()
    needed.need(b)
    needed.need(c2)
    needed.need(d)
    needed.need(e)

    assert sort_resources(needed.resources()) == [a, c, c1, c2, e, b, d]


def test_sort_resources_library_sorting_by_name():
    # these libraries are all at the same level so should be sorted by name
    X = Library('X', '')
    Y = Library('Y', '')
    Z = Library('Z', '')

    a = Resource(X, 'a.js')
    b = Resource(Y, 'b.js')
    c = Resource(Z, 'c.js')

    needed = init_needed()
    needed.need(a)
    needed.need(b)
    needed.need(c)

    assert sort_resources(needed.resources()) == [a, b, c]


def test_sort_resources_library_sorting_by_name_deeper():
    X = Library('X', '')
    Y = Library('Y', '')
    Z = Library('Z', '')

    # only X and Z will be at the same level now
    a = Resource(X, 'a.js')
    c = Resource(Z, 'c.js')
    b = Resource(Y, 'b.js', depends=[a, c])

    needed = init_needed()
    needed.need(b)
    assert sort_resources(needed.resources()) == [a, c, b]


def test_library_nr():
    X = Library('X', '')
    Y = Library('Y', '')
    Z = Library('Z', '')

    # only X and Z will be at the same level now
    a = Resource(X, 'a.js')
    c = Resource(Z, 'c.js')
    b = Resource(Y, 'b.js', depends=[a, c])

    X.init_library_nr()
    Y.init_library_nr()
    Z.init_library_nr()

    assert a.library.library_nr == 0
    assert c.library.library_nr == 0
    assert b.library.library_nr == 1


def test_library_dependency_cycles():
    A = Library('A', '')
    B = Library('B', '')

    a1 = Resource(A, 'a1.js')
    b1 = Resource(B, 'b1.js')
    Resource(A, 'a2.js', depends=[b1])

    # This definition would create a library dependency cycle if permitted.
    with pytest.raises(LibraryDependencyCycleError):
        Resource(B, 'b2.js', depends=[a1])

    # This is an example of an indirect library dependency cycle.
    C = Library('C', '')
    D = Library('D', '')
    E = Library('E', '')
    c1 = Resource(C, 'c1.js')
    Resource(D, 'd1.js', depends=[c1])
    d2 = Resource(D, 'd2.js')
    e1 = Resource(E, 'e1.js', depends=[d2])

    # ASCII ART
    #
    #  C      E      D
    #
    #  c1 <--------- d1
    #
    #  c2 --> e1 --> d2
    #
    with pytest.raises(LibraryDependencyCycleError):
        Resource(C, 'c2.js', depends=[e1])


def test_bundle():
    foo = Library('foo', '')
    a = Resource(foo, 'a.css')
    b = Resource(foo, 'b.css')

    resources = bundle_resources([a, b])
    assert len(resources) == 1
    bundle = resources[0]
    assert bundle.resources() == [a, b]


def test_bundle_dont_bundle_at_the_end():
    foo = Library('foo', '')
    a = Resource(foo, 'a.css')
    b = Resource(foo, 'b.css')
    c = Resource(foo, 'c.css', dont_bundle=True)

    resources = bundle_resources([a, b, c])
    assert len(resources) == 2
    assert resources[0].resources() == [a, b]
    assert resources[-1] is c


def test_bundle_dont_bundle_at_the_start():
    foo = Library('foo', '')
    a = Resource(foo, 'a.css', dont_bundle=True)
    b = Resource(foo, 'b.css')
    c = Resource(foo, 'c.css')

    resources = bundle_resources([a, b, c])
    assert len(resources) == 2
    assert resources[0] is a
    assert resources[1].resources() == [b, c]


def test_bundle_dont_bundle_in_the_middle():
    # now construct a scenario where a dont_bundle resource is in the way
    # of bundling
    foo = Library('foo', '')
    a = Resource(foo, 'a.css')
    b = Resource(foo, 'b.css', dont_bundle=True)
    c = Resource(foo, 'c.css')

    resources = bundle_resources([a, b, c])
    assert len(resources) == 3
    assert resources[0] is a
    assert resources[1] is b
    assert resources[2] is c


def test_bundle_different_renderer():
    # resources with different renderers aren't bundled
    foo = Library('foo', '')
    a = Resource(foo, 'a.css')
    b = Resource(foo, 'b.js')

    resources = bundle_resources([a, b])
    assert len(resources) == 2
    assert resources[0] is a
    assert resources[1] is b


def test_bundle_different_library():
    # resources with different libraries aren't bundled
    l1 = Library('l1', '')
    l2 = Library('l2', '')
    a = Resource(l1, 'a.js')
    b = Resource(l2, 'b.js')

    resources = bundle_resources([a, b])
    assert len(resources) == 2
    assert resources[0] is a
    assert resources[1] is b


def test_bundle_different_directory():
    # resources with different directories aren't bundled
    foo = Library('foo', '')
    a = Resource(foo, 'first/a.css')
    b = Resource(foo, 'second/b.css')

    resources = bundle_resources([a, b])
    assert len(resources) == 2
    assert resources[0] is a
    assert resources[1] is b


def test_bundle_empty_list():
    # we can successfully bundle an empty list of resources
    resources = bundle_resources([])
    assert resources == []


def test_bundle_single_entry():
    # we can successfully bundle a single resource (it's not bundled though)
    foo = Library('foo', '')
    a = Resource(foo, 'a.js')

    resources = bundle_resources([a])
    assert resources == [a]


def test_bundle_single_dont_bundle_entry():
    foo = Library('foo', '')
    a = Resource(foo, 'a.js', dont_bundle=True)

    resources = bundle_resources([a])
    assert resources == [a]


def test_inter_library_dependencies_ordering():
    lib1 = Library('lib1', '')
    lib2 = Library('lib2', '')
    lib3 = Library('lib3', '')
    lib4 = Library('lib4', '')

    js1 = Resource(lib1, 'js1.js')
    js2 = Resource(lib2, 'js2.js', depends=[js1])
    js3 = Resource(lib3, 'js3.js', depends=[js2])

    style1 = Resource(lib3, 'style1.css')
    style2 = Resource(lib4, 'style2.css', depends=[style1])

    needed = init_needed(resources=[js3, style2])
    assert sort_resources(needed.resources()) == \
        [style1, style2, js1, js2, js3]


def test_library_ordering_bug():
    jquery_lib = Library('jquery', '')
    jqueryui_lib = Library('jqueryui', '')
    obviel_lib = Library('obviel', '')
    bread_lib = Library('bread', '')
    app_lib = Library('app', '')

    jquery = Resource(jquery_lib, 'jquery.js')
    jqueryui = Resource(jqueryui_lib, 'jqueryui.js', depends=[jquery])

    obviel = Resource(obviel_lib, 'obviel.js', depends=[jquery])
    obviel_forms = Resource(obviel_lib, 'obviel_forms.js',
                            depends=[obviel])
    obviel_datepicker = Resource(obviel_lib, 'obviel_datepicker.js',
                                 depends=[obviel_forms, jqueryui])

    vtab = Resource(bread_lib, 'vtab.js', depends=[jqueryui])

    tabview = Resource(bread_lib, 'tabview.js', depends=[obviel, vtab])

    bread = Resource(bread_lib, 'bread.js', depends=[tabview, obviel_forms])

    app = Resource(app_lib, 'app.js', depends=[bread, obviel_datepicker])

    needed = init_needed(resources=[app])
    resources = sort_resources(needed.resources())
    for resource in resources:
        print((resource, resource.library.library_nr))
    assert resources == [jquery, jqueryui, obviel, obviel_forms,
                         obviel_datepicker, vtab, tabview, bread, app]

    # assert resources == [obviel, forms, forms_autocomplete, tabview, bread,
    #                     zorgdas]


def test_dummy_needed_should_take_slots_argument():
    needed = get_needed()
    a_resource = object()
    needed.need(a_resource, slots={})
