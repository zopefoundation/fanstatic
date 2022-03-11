from setuptools import setup, find_packages

setup(name='mydevpackage',
      version='1.0.dev',
      include_package_data=True,
      zip_safe=False,
      package_dir={'': 'src'},
      packages=find_packages('src'),
      install_requires=['setuptools', 'fanstatic'],
      entry_points={
          'fanstatic.libraries': [
              'devfoo = mydevpackage:devfoo',
          ]
      })
