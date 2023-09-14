from setuptools import find_packages
from setuptools import setup


try:
    import fanstatic
    cmdclass = {'sdist': fanstatic.sdist_compile}
except ImportError:
    cmdclass = {}

setup(name='somepackage',
      version='1.0dev',
      include_package_data=True,
      zip_safe=False,
      cmdclass=cmdclass,
      package_dir={'': 'src'},
      packages=find_packages('src'),
      install_requires=['setuptools', 'fanstatic'],
      entry_points={
          'fanstatic.libraries': [
              'bar = somepackage.resources:bar',
          ],
          'fanstatic.minifiers': [
              'dummy = somepackage:DUMMY',
          ],
      })
