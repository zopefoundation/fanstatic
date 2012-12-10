from setuptools import setup, Command

long_description = (
    open('README.txt').read()
    + '\n' +
    open('CHANGES.txt').read())


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
    version='0.16',
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
    install_requires=[
        'WebOb >= 1.2'
    ],
    tests_require=[
        'pytest >= 2.0'
    ],
    cmdclass={'test': PyTest},
    entry_points={
        'paste.filter_app_factory': [
            'fanstatic = fanstatic:make_fanstatic',
            'publisher = fanstatic:make_publisher',
            'injector = fanstatic:make_injector',
        ],
        'paste.app_factory': [
            'serf = fanstatic:make_serf',
        ],
    })
