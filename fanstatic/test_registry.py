import py.test

from fanstatic import library_registry, Library

def test_library_registry():
    # the 'foo' library has been placed here by the test buildout
    # fixtures/MyPackage by the entry point mechanism
    assert library_registry.keys() == ['foo']

    # this is a real library, not an entry point
    assert isinstance(library_registry['foo'], Library)

    with py.test.raises(KeyError):
        library_registry['bar']

    bar = Library('bar', '')
    library_registry.add(bar)
    assert library_registry['bar'] is bar
    assert library_registry.keys() == ['foo', 'bar']

    baz = Library('baz', '')
    library_registry[baz.name] = baz
    assert library_registry['baz'] is baz
    assert sorted(library_registry.keys()) == ['bar', 'baz', 'foo']

