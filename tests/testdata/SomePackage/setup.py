from setuptools import setup, find_packages
import fanstatic


setup(name='somepackage',
      version='1.0dev',
      include_package_data=True,
      zip_safe=False,
      cmdclass={'sdist': fanstatic.sdist_compile},
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
