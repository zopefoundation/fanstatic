import pytest

from fanstatic import Library
from fanstatic import get_library_registry
from fanstatic import set_auto_register_library


def test_library_registry():
    set_auto_register_library(False)

    library_registry = get_library_registry()
    library_registry.load_items_from_entry_points()

    # Skip this test if the test fixtures has not been installed.
    pytest.importorskip('mypackage')
    # the 'foo' library has been placed here by the test buildout
    # fixtures/MyPackage by the entry point mechanism
    assert set(library_registry.keys()) == {'foo', 'devfoo'}

    # this is a real library, not an entry point
    assert isinstance(library_registry['foo'], Library)

    with pytest.raises(KeyError):
        library_registry['bar']

    bar = Library('bar', '')
    library_registry.add(bar)
    assert library_registry['bar'] is bar
    assert sorted(library_registry.keys()) == ['bar', 'devfoo', 'foo']

    baz = Library('baz', '')
    library_registry[baz.name] = baz
    assert library_registry['baz'] is baz
    assert sorted(library_registry.keys()) == ['bar', 'baz', 'devfoo', 'foo']

    # MyPackage has been installed in non-development mode:
    assert library_registry['foo'].version is not None
    # MyDevPackage has been installed in development mode:
    assert library_registry['devfoo'].version is None


def test_do_add_library_after_register():
    set_auto_register_library(False)

    library_registry = get_library_registry()
    bar = Library('bar', '')

    assert 'bar' not in library_registry

    library_registry.add(bar)

    assert 'bar' in library_registry

    library_registry.prepare()
    foo = Library('foo', '')

    with pytest.raises(ValueError):
        library_registry.add(foo)
