from setuptools import find_packages
from setuptools import setup


long_description = (
    open('README.rst', encoding='utf8').read()
    + '\n' +
    open('CHANGES.rst', encoding='utf8').read())

install_requires = [
    'WebOb >= 1.2',
    'setuptools',
]

tests_require = [
    'closure',
    'cssmin',
    'jsmin',
    'pytest >= 2.3',
]

setup(
    name='fanstatic',
    version='1.4',
    description="Flexible static resources for web applications",
    classifiers=[
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Development Status :: 5 - Production/Stable'
    ],
    keywords='',
    author='Fanstatic Developers',
    author_email='zope-dev@zope.dev',
    long_description=long_description,
    license='BSD',
    url='http://fanstatic.org',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    zip_safe=False,
    python_requires='>=3.7',
    install_requires=install_requires,
    extras_require={
        'closure': ['closure'],
        'cssmin': ['cssmin'],
        'jsmin': ['jsmin'],
        'test': tests_require,
        'docs': [
            'Sphinx',
        ],
    },
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
