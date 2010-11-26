from setuptools import setup

setup(
    name='fanstatic',
    version='0.11dev',
    description="Flexible static resources for web applications.",
    classifiers=[],
    keywords='',
    author='Fanstatic Developers',
    author_email='fanstatic@googlegroups.com',
    license='BSD',
    url='http://fanstatic.org',
    packages=['fanstatic'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Paste', 'WebOb'],
    extras_require = dict(
        test=['pytest >= 2.0'],
        ),
    entry_points = {
        'paste.filter_app_factory': [
            'publisher = fanstatic.publisher:make_publisher',
            'inject = fanstatic.wsgi:make_inject'],
    })
