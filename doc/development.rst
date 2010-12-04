Developing Fanstatic
====================

You want to contribute to Fanstatic? Great!

Please talk to us on the Fanstatic mailing list:
fanstatic@googlegroups.com

To join us, see: https://groups.google.com/group/fanstatic

Fanstatic's source code is maintained on bitbucket:
http://bitbucket.org/fanstatic

Feel free to fork Fanstatic if you want to hack on it, and send us a
pull request.

Fanstatic requires Python 2.6. 

To install Fanstatic for development, first check it out, then run the
buildout::

 $ python bootstrap.py -d
 $ bin/buildout

This uses Buildout_. Don't worry, that's all you need to know to get
going. The ``-d`` option is to use Distribute_ instead of Setuptools_
and is optional. The buildout process will download and install all
dependencies for Fanstatic.

.. _Buildout: http://buildout.org

.. _Distribute: http://packages.python.org/distribute/

.. _Setuptools: http://pypi.python.org/pypi/setuptools

To run the tests:

  $ bin/py.test

This uses `py.test`_. We love tests, so please write some if you want
to contribute. There are many examples of tests in the ``test_*.py``
modules.

.. _`py.test`: http://pytest.org/

To build the documentation using Sphinx_:

  $ bin/sphinxbuilder

.. _Sphinx: http://sphinx.pocoo.org/

If you use this command, all the dependencies will have been set up
for Sphinx so that the API documentation can be automatically
extracted from the Fanstatic source code. The docs source is in
``doc``, the built documentation will be available in
``doc/_build/html``.

To get a Python prompt with Fanstatic importable (if you want to
experiment on the command-line)::

  $ bin/devpython

You can also run scripts with this if you like::

  $ bin/devpython fanstatictest.py
