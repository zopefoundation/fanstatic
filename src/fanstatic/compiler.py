import argparse
import logging
import os.path
import subprocess
import sys
import time
from shutil import which

import pkg_resources

import setuptools.command.sdist

import fanstatic


mtime = os.path.getmtime

logger = logging.getLogger('fanstatic')


class CompilerError(Exception):
    """A compiler or minifier returned an error.
    """


class Compiler:
    """Generates a target file from a source file.
    """

    name = NotImplemented  # name used to reference this from a Resource
    source_extension = NotImplemented

    def __call__(self, resource, force=False):
        """Perform compilation of ``resource``.

        :param force: If True, always perform compilation. If False (default),\
        only perform compilation if ``should_process`` returns True.
        """
        source = self.source_path(resource)
        target = self.target_path(resource)
        if force or self.should_process(source, target):
            start = time.time()
            self.process(source, target)
            logger.info(
                'Compiling %s in %0.3f seconds', resource, time.time() - start)

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
        """Return an absolute path to the target file (to use as output for
        compilation)
        """
        return resource.fullpath()


class Minifier(Compiler):

    target_extension = NotImplemented

    def source_path(self, resource):
        return resource.fullpath()

    def source_to_target(self, resource):
        return '{}{}'.format(
            os.path.splitext(resource.relpath)[0], self.target_extension)

    def target_path(self, resource):
        # Full path.
        if resource.minified:
            return resource.fullpath(resource.minified)
        return resource.fullpath(self.source_to_target(resource))


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
    parser.add_argument(
        '-v', '--verbose', dest='verbose',
        action='store_true', help='Verbose output')
    options = parser.parse_args()
    if options.verbose:
        # setup logger to output to console
        logging.basicConfig(level=logging.INFO)
    _compile_resources(options.package)


class sdist_compile(setuptools.command.sdist.sdist):

    def run(self):
        self._activate_distribution()
        for package in self.distribution.packages:
            _compile_resources(package)
        # this is kludgy. egg_info does two things, writing egg-info *and*
        # finding all files. But since we generate more files, we need to
        # trigger the finding step again to have them picked up.
        self.get_finalized_command('egg_info').find_sources()
        setuptools.command.sdist.sdist.run(self)  # old-style super()

    def _activate_distribution(self):
        """Make our distribution available in this Python interpreter,
        so that we can access its entry points and import it.
        """
        # find_distributions() needs the egg-info to be able to find anything.
        # Since our superclass runs egg_info as its first action anyway (and
        # commands are run only once), there's no harm in doing it even
        # earlier here.
        self.run_command('egg_info')
        for directory in self.distribution.package_dir.values():
            for dist in pkg_resources.find_distributions(directory):
                pkg_resources.working_set.add(dist)


class NullCompiler(Compiler):
    """Null object (no-op compiler), that will be used when compiler/minifier
    on a Resource is set to None.
    """

    name = None

    def source_path(self, resource):
        return None

    def target_path(self, resource):
        return None

    def should_process(self, source, target):
        return False


SOURCE = object()
TARGET = object()


class CommandlineBase:

    command = NotImplemented
    arguments = []

    @property
    def available(self):
        if os.path.exists(self.command):
            return True
        return which(self.command) is not None

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
        p = super().process(source, target)
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
    source_extension = '.scss'
    arguments = [SOURCE, TARGET]


SASS_COMPILER = SASS()


class PythonPackageBase:

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
            raise CompilerError('Package `%s` not available.' % self.package)


class CSSMin(PythonPackageBase, Minifier):

    name = 'cssmin'
    package = 'cssmin'
    target_extension = '.min.css'

    def process(self, source, target):
        cssmin = self._import()
        with open(target, 'wb') as output:
            with open(source) as input:
                css = input.read()
                output.write(cssmin.cssmin(css).encode('utf-8'))


CSSMIN_MINIFIER = CSSMin()


class JSMin(PythonPackageBase, Minifier):

    name = 'jsmin'
    package = 'jsmin'
    target_extension = '.min.js'

    def process(self, source, target):
        jsmin = self._import()
        with open(target, 'wb') as output:
            with open(source) as input:
                js = input.read()
                output.write(jsmin.jsmin(js).encode('utf-8'))


JSMIN_MINIFIER = JSMin()


class Closure(PythonPackageBase, Minifier):
    # Hey, a PythonPackageBase with CommandlineBase behavior.
    # We use the 'closure' python package in order to have a reference to th
    # jar file that is easy to find from python and to be able to control the
    # version of the dependency through python package management in stead of
    # leaving this to the OS.
    name = 'closure'
    package = 'closure'
    target_extension = '.min.js'
    arguments = [
        '--charset', 'UTF-8',
        '--compilation_level', 'WHITESPACE_ONLY',
    ]

    def process(self, source, target):
        python_closure = self._import()
        cmd = ['java', '-jar', python_closure.get_jar_filename()]
        cmd.extend(self.arguments)
        cmd.extend(['--js', source, '--js_output_file', target])
        p = subprocess.Popen(' '.join(cmd), shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        if p.returncode != 0:
            raise CompilerError(p.stderr.read())
        return p


CLOSURE_MINIFIER = Closure()
