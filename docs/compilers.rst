Compilers and Minifiers
=======================

.. py:module:: fanstatic


Fanstatic supports running external programs to create transformations of
resource files. There are two use cases for this: The first use case is
compiling files written in languages like CoffeeScript or SASS into JavaScript
and CSS, respectively. The second use case is automatically generating minified
versions of JS and CSS files. We call programs for the first case `compilers`
and those for the second case `minifiers`, and use `compiling` as the
encompassing term.


Running compilers
-----------------

There are two ways of running compilers, one is manually via the command-line
program ``fanstatic-compile``. The other way is on-the-fly when processing a
request: When the `compile` option is set to True (see :doc:`configuration`),
Fanstatic will check on each request whether the source file is older than the
compiled file, and invoke the compiler if needed.

::

  Usage: fanstatic-compile my.package.name
  Compiles and minifies all Resources declared in the given package.


Fanstatic also provides a hook into ``setuptools`` to run compilers during
sdist creation, so you can package and deploy the compiled resources and don't
need any of the compilers in the production environment. To use this, add the
following to the ``setup()`` call in your package's ``setup.py``::

  setup(
    ...
    cmdclass={'sdist': fanstatic.sdist_compile},
    ...
  )

Then, run ``python setup.py sdist`` as usual to create your sdist.

Note: If you are using version control plugins (e.g. ``setuptools_hg``) to
collect the files to include in your sdist, and do not check in the
compiled/minified files, they will not be included in the sdist. In that case,
you will need to create a ``MANIFEST.in`` file to pick them up, for example::

  recursive-include src *.css *.js


Configuring compilers
---------------------

Compilers work by creating the resource file from a source file. For example,
the CoffeeScript compiler creates ``foo.js`` from ``foo.coffee``. This is
configured like so::

  from fanstatic import Library, Resource

  js_library = Library('js', 'js_resources')

  a = Resource(js_library, 'a.js', compiler='coffee', source='a.coffee')

When compilation is run and ``a.js`` is not present, or older than
``a.coffee``, Fanstatic will run the CoffeeScript compiler on ``a.coffee`` to
produce ``a.js``.

Compilers can have knowledge what the source files are typically named, so
usually you don't have to specify that explicitly on each Resource (if you do
specify a ``source`` that of course is used, overriding what the Compiler
thought).

You can also configure compilers on the level of the Library, so they apply to
all Resources with a given extension::

  from fanstatic import Library, Resource

  coffee_library = Library('coffee', 'coffee_resources',
                           compilers={'.js': 'coffee'})

  a = Resource(coffee_library, 'b.js')
  b = Resource(coffee_library, 'plain.js', compiler=None)

Note that individual Resources can override the compiler set on the Library.


Configuring minifiers
---------------------

Minifiers work by creating a minified version of the resource file. For
example, jsmin creates ``foo.min.js`` from ``foo.js``. This is configured
like so::

  from fanstatic import Library, Resource

  js_library = Library('js', 'js_resources')

  a = Resource(js_library, 'a.js', minified='a.min.js', minifier='jsmin')

Minifiers can have a built-in rule what the target filename looks like, so
usually you don't have to explicitly specify ``minified=``.

You can also configure minifiers on the level of the Library, so they apply to
all Resources with a given extension::

  from fanstatic import Library, Resource

  js_library = Library('js', 'js_resources', minifiers={'.js': 'jsmin'})

  a = Resource(js_library, 'a.js')
  b = Resource(js_library, 'tricky.js', minifier=None, minified='tricky.min.js')

Note that individual Resources can override the minifier set on the Library.

Pre-packaged compilers
----------------------

Fanstatic includes the following compilers:

:coffee: `CoffeeScript`_, a little language that compiles to JavaScript,
         requires the ``coffee`` binary (``npm install -g coffeescript``)
:less: `LESS`_, the dynamic stylesheet language,
       requires the ``lessc`` binary (``npm install -g less``)
:sass: `SASS`_, Syntactically Awesome Stylesheets,
       requires the ``sass`` binary (``gem install sass``)

.. _`CoffeeScript`: http://coffeescript.org/
.. _`LESS`: http://lesscss.org/
.. _`SASS`: http://sass-lang.com/


Fanstatic includes the following minifiers:

:cssmin: `cssmin <https://pypi.org/project/cssmin>`_, A Python port of the YUI CSS compression algorithm,
  requires the ``cssmin`` package.  Use the extras requirement
  ``fanstatic[cssmin]`` to install this dependency.
:jsmin: `jsmin <https://pypi.org/project/jsmin>`_, A Python port of Douglas Crockford's ``jsmin``, requires
  the ``jsmin`` package. Use the extras requirement
  ``fanstatic[jsmin]`` to install this dependency.
:closure: `closure <https://pypi.org/project/closure>`_, A Python wrapper around the
  `Google Closure Compiler`_. Use the extras requirement
  ``fanstatic[closure]`` to install this dependency.

.. _`Google Closure Compiler`: https://developers.google.com/closure/compiler/


Hiding source files
-------------------

You can prevent the Fanstatic publisher from serving the source files
in by using the :doc:`ignores <configuration>` configuration option.

Writing compilers
-----------------

A compiler is a class that conforms to the following interface:

.. autoclass:: fanstatic.compiler.Compiler
  :special-members:
  :members:

Fanstatic provides generic base classes for both compilers and minifiers, as
well as helper classes for compilers that run external commands or depend on
other Python packages (:py:class:`fanstatic.compiler.CommandlineBase`,
:py:class:`fanstatic.compiler.PythonPackageBase`).

To make a compiler or minifier known to Fanstatic, it needs to be declared as
an `entry point` in its packages' ``setup.py``::

  entry_points={
      'fanstatic.compilers': [
          'coffee = fanstatic.compiler:COFFEE_COMPILER',
          ],
      'fanstatic.minifiers': [
          'jsmin = fanstatic.compiler:JSMIN_MINIFIER',
          ],
      },
