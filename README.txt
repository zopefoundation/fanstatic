README
======

Fanstatic is a smart static resource publisher for Python. For more
information on what it's about and how to use it, see:
http://fanstatic.org

If you want to hack on Fanstatic, here are some brief instructions.

To install for development::

 $ python bootstrap.py -d
 $ bin/buildout

The ``-d`` option is to use Distribute instead of Setuptools and is
optional. This will download and install all dependencies for
Fanstatic.

To run the tests:

  $ bin/py.test

To build the documentation using Sphinx:

  $ bin/sphinxbuilder
