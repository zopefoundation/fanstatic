import pytest

from fanstatic import ConfigurationError
from fanstatic import Library
from fanstatic import Resource
from fanstatic import init_needed
from fanstatic import make_injector
from fanstatic.injector import InjectorPlugin
from fanstatic.injector import TopBottomInjector
from fanstatic.registry import InjectorRegistry


class TopInjector(InjectorPlugin):

    name = 'top'

    def __call__(self, html, needed):
        needed_html = self.make_inclusion(needed).render()
        return html.replace(b'<head>', f'<head>{needed_html}'.encode(), 1)


def test_injector_based_on_injectorplugin():
    foo = Library('foo', '')
    a = Resource(foo, 'a.css')
    b = Resource(foo, 'b.css', bottom=True)
    needed = init_needed(resources=[a, b])

    inj = TopInjector({})

    html = b'<html><head></head><body></body></html>'

    assert inj(html, needed) == \
        b'''<html><head><link rel="stylesheet" type="text/css" href="/fanstatic/foo/a.css" />
<link rel="stylesheet" type="text/css" href="/fanstatic/foo/b.css" /></head><body></body></html>'''  # noqa: E501 line too long


class MockRegistry:

    def __init__(self, request):
        self.request = request

    def add_injector(self, injector):
        return self._register_injector(InjectorRegistry, injector)

    def _register_injector(self, registry, injector):
        self.request.addfinalizer(
            lambda: registry.instance().pop(injector.name))
        registry.instance().add(injector)
        return injector


@pytest.fixture
def injectors(request):
    return MockRegistry(request)


def test_injector_plugin_registered_by_name(injectors):
    with pytest.raises(KeyError):
        InjectorRegistry.instance()['top']

    injectors.add_injector(TopInjector)

    # After registering, no longer raise a key error.
    InjectorRegistry.instance()['top']


def test_wsgi_middleware_lookup_injector():
    injector_middleware = make_injector(None, {})
    # Default is the topbottom injector
    assert isinstance(injector_middleware.injector, TopBottomInjector)

    with pytest.raises(ConfigurationError):
        make_injector(None, {}, injector='foo')


def test_wsgi_middleware_lookup_injector_register(injectors):
    with pytest.raises(ConfigurationError):
        make_injector(None, {}, injector='top')

    injectors.add_injector(TopInjector)

    # After registering, no longer raise a Configuration Error.
    make_injector(None, {}, injector='top')
