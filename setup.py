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
        import sys,subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)

setup(
    name='fanstatic',
    version='0.14a',
    description="Flexible static resources for web applications.",
    classifiers=[],
    keywords='',
    author='Fanstatic Developers',
    author_email='fanstatic@googlegroups.com',
    long_description=long_description,
    license='BSD',
    url='http://fanstatic.org',
    packages=['fanstatic'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'WebOb >= 1.2'
    ],
    extras_require = dict(
        test=['pytest >= 2.0'],
        ),
    cmdclass = {'test': PyTest},
    entry_points = {
        'paste.filter_app_factory': [
            'fanstatic = fanstatic:make_fanstatic',
            'publisher = fanstatic:make_publisher',
            'injector = fanstatic:make_injector',
            ],
        'paste.app_factory': [
            'serf = fanstatic:make_serf',
            ],
    })
