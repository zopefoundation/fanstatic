from setuptools import setup, Command
import sys

long_description = (
    open('README.txt').read()
    + '\n' +
    open('CHANGES.txt').read())


install_requires = [
    'WebOb >= 1.2',
    'setuptools',
]

if sys.version_info < (2, 7):
    install_requires.append('argparse')

if sys.version_info < (3,):
    install_requires.append('which')
else:
    install_requires.append('which==1.1.3.py3')

tests_require = [
    'closure',
    'cssmin',
    'jsmin',
    'pytest >= 2.3',
    'pytest-capturelog',
]

class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys
        import subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)

setup(
    name='fanstatic',
    version='1.0a4',
    description="Flexible static resources for web applications",
    classifiers=[
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Development Status :: 5 - Production/Stable'
    ],
    keywords='',
    author='Fanstatic Developers',
    author_email='fanstatic@googlegroups.com',
    long_description=long_description,
    license='BSD',
    url='http://fanstatic.org',
    packages=['fanstatic'],
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'closure': ['closure'],
        'cssmin': ['cssmin'],
        'jsmin': ['jsmin'],
        'test': tests_require,
    },
    cmdclass={'test': PyTest},
    entry_points={
        'console_scripts': [
            'fanstatic-compile = fanstatic.compiler:compile_resources',
        ],
        'paste.filter_app_factory': [
            'fanstatic = fanstatic:make_fanstatic',
            'injector = fanstatic:make_injector',
        ],
        'paste.app_factory': [
            'serf = fanstatic:make_serf',
            'publisher = fanstatic:make_publisher',
        ],
        'fanstatic.injectors': [
            'topbottom = fanstatic.injector:TopBottomInjector',
        ],
        'fanstatic.compilers': [
            'coffee = fanstatic.compiler:COFFEE_COMPILER',
            'less = fanstatic.compiler:LESS_COMPILER',
            'sass = fanstatic.compiler:SASS_COMPILER',
        ],
        'fanstatic.minifiers': [
            'cssmin = fanstatic.compiler:CSSMIN_MINIFIER',
            'jsmin = fanstatic.compiler:JSMIN_MINIFIER',
            'closure = fanstatic.compiler:CLOSURE_MINIFIER',
        ]
    })
