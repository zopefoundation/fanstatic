from fanstatic import Library, Resource, NeededResources
from fanstatic.compiler import Compiler, Minifier
import fanstatic
import os
import pytest
import time


class MockCompiler(object):

    name = 'mock'

    def __init__(self):
        self.calls = []

    def __call__(self, resource):
        self.calls.append(resource)


class TestingRegistry(object):

    def __init__(self, request):
        self.request = request

    def add_compiler(self, compiler):
        return self._register_compiler(
            fanstatic.CompilerRegistry, compiler)

    def add_minifier(self, compiler):
        return self._register_compiler(
            fanstatic.MinifierRegistry, compiler)

    def _register_compiler(self, registry, compiler):
        self.request.addfinalizer(
            lambda: registry.instance().pop(compiler.name))
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
    compilers.add_compiler(MockCompiler())
    compilers.add_minifier(MockCompiler())

    lib = Library('lib', '')
    a = Resource(lib, 'a.js', compiler='mock', minifier='mock')

    needed = NeededResources()
    needed.need(a)
    needed.render()
    assert not compilers.compiler('mock').calls
    assert not compilers.minifier('mock').calls


def test_setting_compile_True_should_call_compiler_and_minifier(
    compilers):
    compilers.add_compiler(MockCompiler())
    compilers.add_minifier(MockCompiler())
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


def test_compiler_target_is_full_resource_path():
    lib = Library('lib', '/foo')
    a = Resource(lib, 'a.js')
    compiler = Compiler()
    assert compiler.target_path(a) == '/foo/a.js'


def test_compiler_is_source_if_given_on_resource():
    lib = Library('lib', '/foo')
    a = Resource(lib, 'a.js', source='a.source')
    compiler = Compiler()
    assert compiler.source_path(a) == '/foo/a.source'


def test_compiler_source_transforms_extension_if_no_source_given():
    lib = Library('lib', '/foo')
    a = Resource(lib, 'a.js')
    compiler = Compiler()
    compiler.source_extension = '.source'
    assert compiler.source_path(a) == '/foo/a.source'


def test_minifier_source_is_full_resource_path():
    lib = Library('lib', '/foo')
    a = Resource(lib, 'a.js')
    minifier = Minifier()
    assert minifier.source_path(a) == '/foo/a.js'


def test_minifier_target_is_minified_if_given_on_resource():
    lib = Library('lib', '/foo')
    a = Resource(lib, 'a.js', minified='a.min.js')
    minifier = Minifier()
    assert minifier.target_path(a) == '/foo/a.min.js'


def test_minifier_target_transforms_extension_if_no_name_given():
    lib = Library('lib', '/foo')
    a = Resource(lib, 'a.js')
    minifier = Minifier()
    minifier.target_extension = '.min.js'
    assert minifier.target_path(a) == '/foo/a.min.js'


def test_should_process_if_target_does_not_exist(tmpdir):
    assert Compiler().should_process(None, str(tmpdir / 'target'))


def test_should_process_if_target_is_older_than_source(tmpdir):
    source = str(tmpdir / 'source')
    open(source, 'w').close()
    target = str(tmpdir / 'target')
    open(target, 'w').close()
    old = time.time() - 1
    os.utime(target, (old, old))
    assert Compiler().should_process(source, target)


def test_should_not_process_if_target_is_newer_than_source(tmpdir):
    source = str(tmpdir / 'source')
    open(source, 'w').close()
    target = str(tmpdir / 'target')
    open(target, 'w').close()
    old = time.time() - 1
    os.utime(source, (old, old))
    assert not Compiler().should_process(source, target)
