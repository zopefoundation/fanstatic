from which import which, WhichError as NotFound
import argparse
import fanstatic
import os.path
import subprocess
import sys

mtime = os.path.getmtime


class CompilerError(Exception):
    """A compiler or minifier returned an error.
    """


class Compiler(object):
    """Generates a target file from a source file.
    """

    name = NotImplemented  #: name used to reference this from a Resource
    source_extension = NotImplemented

    def __call__(self, resource, force=False):
        """Perform compilation of ``resource``.

        :param force: If True, always perform compilation. If False (default),\
        only perform compilation if ``should_process`` returns True.
        """

        source = self.source_path(resource)
        target = self.target_path(resource)
        if force or self.should_process(source, target):
            self.process(source, target)

    def process(self, source, target):
        pass  # Override in subclass

    def should_process(self, source, target):
        """
        Determine whether to process the resource, based on the mtime of the
        target and source.
        """
        return not os.path.isfile(target) or mtime(source) > mtime(target)

    @property
    def available(self):
        """Whether this compiler is available, i.e. necessary dependencies
        like external commands or third-party packages are installed.
        """
        return False  # Override in subclass

    def source_path(self, resource):
        """Return an absolute path to the source file (to use as input for
        compilation)
        """
        if resource.source:
            return resource.fullpath(resource.source)
        return os.path.splitext(resource.fullpath())[0] + self.source_extension

    def target_path(self, resource):
        """Return an absolute path to the target file (to use as ouput for
        compilation)
        """
        return resource.fullpath()


class Minifier(Compiler):

    target_extension = NotImplemented

    def source_path(self, resource):
        return resource.fullpath()

    def target_path(self, resource):
        if resource.minified:
            return resource.fullpath(resource.minified)
        return resource.fullpath(
            os.path.splitext(resource.relpath)[0] + self.target_extension)


def _compile_resources(package):
    for library in fanstatic.LibraryRegistry.instance().values():
        if not library.module.startswith(package):
            continue
        for resource in library.known_resources.values():
            resource.compile(force=True)


def compile_resources(argv=sys.argv):
    parser = argparse.ArgumentParser(
        description='Compiles and minifies all Resources'
        ' declared in the given package.')
    parser.add_argument(
        'package', help='Dotted name of the package to compile')
    options = parser.parse_args()
    _compile_libraries(options.package)


class NullCompiler(Compiler):
    """Null object (no-op compiler), that will be used when compiler/minifier
    on a Resource is set to None.
    """

    name = None

    def source_path(self, resource):
        return None

    def target_path(self, resource):
        return None


SOURCE = object()
TARGET = object()


class CommandlineBase(object):

    command = NotImplemented
    arguments = []

    @property
    def available(self):
        if os.path.exists(self.command):
            return True
        try:
            return bool(which(self.command))
        except NotFound:
            return False

    def process(self, source, target):
        cmd = [self.command] + self._expand(self.arguments, source, target)
        p = subprocess.Popen(' '.join(cmd), shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        if p.returncode != 0:
            raise CompilerError(p.stderr.read())
        return p

    def _expand(self, arguments, source, target):
        result = []
        for arg in arguments:
            if arg is SOURCE:
                arg = source
            elif arg is TARGET:
                arg = target
            result.append(arg)
        return result


class CoffeeScript(CommandlineBase, Compiler):

    name = 'coffee'
    command = 'coffee'
    arguments = ['--compile', '--bare', '--print', SOURCE]

    def process(self, source, target):
        p = super(CoffeeScript, self).process(source, target)
        with open(target, 'wb') as output:
            output.write(p.stdout.read())

COFFEE_COMPILER = CoffeeScript()


class LESS(CommandlineBase, Compiler):

    name = 'less'
    command = 'lessc'
    arguments = [SOURCE, TARGET]

LESS_COMPILER = LESS()


class SASS(CommandlineBase, Compiler):

    name = 'sass'
    command = 'sass'
    arguments = [SOURCE, TARGET]

SASS_COMPILER = SASS()


class PythonPackageBase(object):

    package = ''

    @property
    def available(self):
        try:
            self._import()
        except CompilerError:
            return False
        else:
            return True

    def _import(self):
        try:
            return __import__(self.package, globals=globals(), fromlist=[''])
        except ImportError:
            raise CompilerError('Package `cssmin` not available.')


class CSSMin(PythonPackageBase, Minifier):

    name = 'cssmin'
    package = 'cssmin'

    def process(self, source, target):
        cssmin = self._import()
        with open(target, 'wb') as output:
            css = open(source, 'r').read()
            output.write(cssmin.cssmin(css))

CSSMIN_MINIFIER = CSSMin()


class JSMin(PythonPackageBase, Minifier):

    name = 'jsmin'
    package = 'jsmin'

    def process(self, source, target):
        jsmin = self._import()
        with open(target, 'wb') as output:
            js = open(source, 'r').read()
            output.write(jsmin.jsmin(js))

JSMIN_MINIFIER = JSMin()
