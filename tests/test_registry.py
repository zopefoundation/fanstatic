import pytest

from fanstatic import get_library_registry, Library, compat


def test_library_registry():
    # Skip this test if the test fixtures has not been installed.
    pytest.importorskip('mypackage')

    library_registry = get_library_registry()
    # the 'foo' library has been placed here by the test buildout
    # fixtures/MyPackage by the entry point mechanism
    assert compat.dict_keys(library_registry) == ['foo']

    # this is a real library, not an entry point
    assert isinstance(library_registry['foo'], Library)

    with pytest.raises(KeyError):
        library_registry['bar']

    bar = Library('bar', '')
    library_registry.add(bar)
    assert library_registry['bar'] is bar
    assert sorted(compat.dict_keys(library_registry)) == ['bar', 'foo']

    baz = Library('baz', '')
    library_registry[baz.name] = baz
    assert library_registry['baz'] is baz
    assert sorted(compat.iterkeys(library_registry)) == ['bar', 'baz', 'foo']

    # MyPackage has been installed in development mode:
    assert library_registry['foo'].version is None
