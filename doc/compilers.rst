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

XXX explain usage of fanstatic-compile

XXX setuptools or zest.releaser-plugin?


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
                           compilers={'js': 'coffee'})

  a = Resource(coffee_library, 'b.js')
  b = Resource(coffee_library, 'plain.js', compiler=None)

Note that individual Resources can override the compiler set on the Library.


Configuring minifiers
---------------------

Minifiers work by creating a minified version of the resource file. For
example, uglifyjs creates ``foo.min.js`` from ``foo.js``. This is configured
like so::

  from fanstatic import Library, Resource

  js_library = Library('js', 'js_resources')

  a = Resource(js_library, 'a.js', minified='a.min.js', minifier='uglifys')

Minifiers can have a built-in rule what the target filename looks like, so
usually you don't have to explicitly specify ``minified=``.

You can also configure minifiers on the level of the Library, so they apply to
all Resources with a given extension::

  from fanstatic import Library, Resource

  js_library = Library('js', 'js_resources', minifiers={'js': 'uglifys'})

  a = Resource(js_library, 'a.js')
  b = Resource(js_library, 'tricky.js', minifier=None, minified='tricky.min.js')

Note that individual Resources can override the minifier set on the Library.


Writing compilers
-----------------

A compiler is a class that conforms to the following interface:

XXX describe compiler/minifier API

As seen above, compilers and minifiers are configured using a string name.
To make a compiler or minifier known to Fanstatic, it needs to be declared as
an `entry point` in its packages' ``setup.py``::

  entry_points={
      'fanstatic.compilers': [
          'coffee = js.coffeescript:compiler',
          ],
      'fanstatic.minifiers': [
          'uglifyjs = js.uglifys:minifier',
          ],
      },
