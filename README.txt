README
======

Fanstatic is a smart static resource publisher for Python. For more
information on what it's about and how to use it, see:
http://fanstatic.org

If you want to hack on Fanstatic, here are some brief instructions.

The Fanstatic mailing list is: fanstatic@googlegroups.com

Fanstatic is on bitbucket: http://bitbucket.org/fanstatic

Feel free to fork Fanstatic if you want to hack on it, and send us a
pull request.

To install Fanstatic for development, first check it out, then::

 $ python bootstrap.py -d
 $ bin/buildout

The ``-d`` option is to use Distribute instead of Setuptools and is
optional. The buildout process will download and install all
dependencies for Fanstatic.

To run the tests:

  $ bin/py.test

To build the documentation using Sphinx:

  $ bin/sphinxbuilder

To get a Python with Fanstatic importable (if you want to experiment 
on the command-line)::

  $ bin/devpython
