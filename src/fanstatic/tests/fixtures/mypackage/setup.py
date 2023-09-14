from setuptools import find_packages
from setuptools import setup


setup(name='mypackage',
      version='1.0',
      include_package_data=True,
      zip_safe=False,
      package_dir={'': 'src'},
      packages=find_packages('src'),
      install_requires=['setuptools', 'fanstatic'],
      entry_points={
          'fanstatic.libraries': [
              'foo = mypackage:foo',
          ]
      })
