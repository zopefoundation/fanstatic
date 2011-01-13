Creating a Resource Library
===========================

.. py:module:: fanstatic

We've seen how to reuse existing resources, but how do you publish
your own resources using Fanstatic?

Here's how:

Your project
------------

So, you're developing a Python project. It's set up in the standard
Python way, along these lines::

  fooproject/
     setup.py
     foo/
       __init__.py

Making Fanstatic available in your project
------------------------------------------

In order to be able to import from ``fanstatic`` in your project,
you need to make it available first. The standard way is to include it
in ``setup.py``, like this::

    install_requires=[
        'fanstatic',
    ]

Adding the resource directory
-----------------------------

You need to place the resources in a subdirectory somewhere in your
Python code.

Imagine you have some resources in a directory called
``bar_resources``. You simply place this in your package::

  fooproject/
     setup.py
     foo/
       __init__.py
       bar_resources/
         a.css
         b.js

Note that ``bar_resources`` isn't a Python package, so it doesn't have
an ``__init__.py``. It's just a directory.

Declaring the Library
---------------------

You need to declare a :py:class:`Library` for ``bar``. In
``__init__.py`` (or any module in the package), write the following::

  from fanstatic import Library

  bar_library = Library('bar', 'bar_resources')

Here we construct a fanstatic Library named ``bar``, and we point to
the subdirectory `bar_resources` to find them.

Hooking it up to an entry point
-------------------------------

To let Fanstatic know that this library exists so it will
automatically publish it, we need to add an `entry point` for the
library to your project's ``setup.py``. Add this to the ``setup()``
function::

    entry_points={
        'fanstatic.libraries': [
            'bar = foo:bar_library',
            ],
        },

This tells Fanstatic that there is a ``Library`` instance in the
``foo`` package. What if you had defined the library not in
``__init__.py`` but in a module, such as ``foo.qux``? You would have
referred to it using ``foo.qux:bar_library``.

.. _`entry point`: http://reinout.vanrees.org/weblog/2010/01/06/zest-releaser-entry-points.html

At this stage, Fanstatic can serve the resources in your library. The
default URLS are::

  /fanstatic/bar/a.css

  /fanstatic/bar/b.js

Declaring resources for inclusion
---------------------------------

While now the resources can be served, we can't actually yet
``.need()`` them, so that we can have Fanstatic include them on web
pages for us. For this, we need to create :py:class:`Resource`
instances. Let's modify our original ``__init__.py`` to read like
this::

  from fanstatic import Library, Resource

  bar_library = Library('bar', 'bar_resources')

  a = Resource(bar_library, 'a.css')

  b = Resource(bar_library, 'b.js')

Now we're done!

Depending on resources
----------------------

We can start using the resources in our code now. To make sure
``b.js`` is included in our web page, we can do this anywhere in our
code::

  from foo import b

  ...

  def somewhere_deep_in_our_code():
      b.need()

An example
----------

Need an example where it's all put together? We maintain a Fanstatic
package called ``js.jquery`` that wraps jQuery this way:

  http://bitbucket.org/fanstatic/js.jquery/src

It's also available on PyPI:

  http://pypi.python.org/pypi/js.jquery

Bonus: shipping the library
---------------------------

You can declare any number of libraries and resources in your
application. What if you want to reuse a library in multiple
applications? That's easy too: you just put your library, library
entry point, resource definitions and resource files in a separate
Python project. You can then use this in your application projects. If
it's useful to other as well, you can also publish it on PyPi_! The
various ``js.*`` projects that we are maintaining for Fanstatic, such
as ``js.jquery``, are already examples of this.

.. _PyPi: http://pypi.python.org

Bonus: dependencies between resources
-------------------------------------

What if we really want to include ``a.css`` whenever we pull in
``b.js``, as code in ``b.js`` depends on it? Change your code to this::

  from fanstatic import Library, Resource

  bar_library = Library('bar', 'bar_resources')

  a = Resource(bar, 'a.css')

  b = Resource(bar, 'b.js', depends=[a])

Whenever you ``.need()`` ``b`` now, you'll also get ``a`` included on
your page.

You can also use a :py:class:`GroupResource` to group Resources together::

  from fanstatic import GroupResource

  c = GroupResource([a, b])

Bonus: a minified version
-------------------------

What if you have a minified version of your ``b.js`` Javascript called
``b.min.js`` available in the ``bar_resources`` directory and you want
to let Fanstatic know about it? You just write this::

  from fanstatic import Library, Resource

  bar_library = Library('bar', 'bar_resources')

  a = Resource(bar, 'a.css')

  b = Resource(bar, 'b.js', minified='b.min.js')

If you now configure Fanstatic to use the ``minified`` mode, it will
automatically pull in ``b.min.js`` instead of ``b.js`` whenever you do
``b.need()``.
