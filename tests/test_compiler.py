from fanstatic import Library, Resource, NeededResources
import fanstatic
import pytest


class MockCompiler(object):

    name = 'mock'

    def __init__(self):
        self.calls = []

    def __call__(self, resource):
        self.calls.append(resource)


class TestingRegistry(object):

    def __init__(self, request):
        self.request = request

    def add_compiler(self, compiler_class):
        return self._register_compiler(
            fanstatic.CompilerRegistry, compiler_class)

    def add_minifier(self, compiler_class):
        return self._register_compiler(
            fanstatic.MinifierRegistry, compiler_class)

    def _register_compiler(self, registry, compiler_class):
        self.request.addfinalizer(
            lambda: registry.instance().pop(compiler_class.name))
        compiler = compiler_class()
        registry.instance().add(compiler)
        return compiler

    def compiler(self, name):
        return fanstatic.CompilerRegistry.instance()[name]

    def minifier(self, name):
        return fanstatic.MinifierRegistry.instance()[name]


@pytest.fixture
def compilers(request):
    return TestingRegistry(request)


def test_setting_compile_False_should_not_call_compiler_and_minifier(
    compilers):
    compilers.add_compiler(MockCompiler)
    compilers.add_minifier(MockCompiler)

    lib = Library('lib', '')
    a = Resource(lib, 'a.js', compiler='mock', minifier='mock')

    needed = NeededResources()
    needed.need(a)
    needed.render()
    assert not compilers.compiler('mock').calls
    assert not compilers.minifier('mock').calls


def test_setting_compile_True_should_call_compiler_and_minifier(
    compilers):
    compilers.add_compiler(MockCompiler)
    compilers.add_minifier(MockCompiler)
    lib = Library('lib', '')
    a = Resource(lib, 'a.js', compiler='mock', minifier='mock')

    needed = NeededResources(compile=True)
    needed.need(a)
    needed.render()

    mock_compiler = compilers.compiler('mock')
    mock_minifier = compilers.minifier('mock')
    assert len(mock_compiler.calls) == 1
    assert mock_compiler.calls[0] == a
    assert len(mock_minifier.calls) == 1
    assert mock_minifier.calls[0] == a
