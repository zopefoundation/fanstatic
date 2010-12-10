Developing Fanstatic
====================

You want to contribute to Fanstatic? Great!

Please talk to us our on our :ref:`mailing list <mailing list>` about
your plans!

Sources
-------

Fanstatic's source code is maintained on bitbucket:
http://bitbucket.org/fanstatic

You can check out fanstatic using `Mercurial`_ (hg); see the bitbucket_
documentation for more information as well.

.. _`Mercurial`: http://mercurial.selenic.com/

.. _`bitbucket`: http://bitbucket.org

Feel free to fork Fanstatic on bitbucket if you want to hack on it,
and send us a pull request when you want us to merge your
improvements.

Development install of Fanstatic
--------------------------------

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

Tests
-----

To run the tests::

  $ bin/py.test

This uses `py.test`_. We love tests, so please write some if you want
to contribute. There are many examples of tests in the ``test_*.py``
modules.

.. _`py.test`: http://pytest.org/

Test coverage
-------------

To get a test coverage report::

  $ bin/py.test --cov fanstatic

To get a report with more details::

   bin/py.test --cov-report html --cov fanstatic

The results will be stored in a subdirectory ``htmlcov``. You can point
a web browser to its ``index.html`` to get a detailed coverage report.

Building the documentation
--------------------------

To build the documentation using Sphinx_::

  $ bin/sphinxbuilder

.. _Sphinx: http://sphinx.pocoo.org/

If you use this command, all the dependencies will have been set up
for Sphinx so that the API documentation can be automatically
extracted from the Fanstatic source code. The docs source is in
``doc``, the built documentation will be available in
``doc/_build/html``.

Python with Fanstatic on the sys.path
-------------------------------------

It's often useful to have a project and its dependencies available for
import on a Python prompt for experimentation:

  $ bin/devpython

You can now import fanstatic::

  >>> import fanstatic

You can also run your own scripts with this custom interpreter if you
like::

  $ bin/devpython somescript.py

This can be useful for quick experimentation. When you want to use
Fanstatic in your own projects you would normally include it in your
project's ``setup.py`` dependencies instead.

Releases
--------

The buildout also installs `zest.releaser`_ which can be used to make
automatic releases to PyPI (using ``bin/fullrelease``).

.. _`zest.releaser`: http://pypi.python.org/pypi/zest.releaser


