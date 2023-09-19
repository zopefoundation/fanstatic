=======
CHANGES
=======

1.4 (2023-09-19)
================

- Drop Python 2 leftovers. (Support was dropped in 1.2)

- Add a bare miminumal readthedocs config file as per:

  https://blog.readthedocs.com/migrate-configuration-v2/

- Add support for Python 3.7, 3.11.


1.3 (2022-12-21)
================

- Add support for Python 3.9 and 3.10.
  Conditional support for shutilwhich for older python versions.

- Fix Trove classifiers.

- Move tests to GitHub Actions.

- Make documentation buildable with Python 3.


1.2 (2022-03-11)
================

Features
--------

- Use the packaging version parsing to determine whether a fanstatic library
  is installed from a dev package, and set the Library version accordingly.

Backwards incompatible changes
------------------------------

- Drop support for Python 2, 3.5, 3.6, 3.7.

Documentation
-------------

- Update documentation to reflect the current place of repositories at GitHub.


1.1 (2019-01-22)
================

Backwards incompatible changes
------------------------------

- Drop support for Python 2.6, 3.2 and 3.3.

Other changes
-------------

- Add support for Python 3.5, 3.6 and 3.7.


1.0.0 (2018-01-16)
==================
- Fixup tests for new versions of dependencies and changed contracts. This
  also improves Python 3 compatibility.

1.0a7 (2015-11-07)
==================

- Make sure the registry is prepared if only the publisher is used
  within a process.

- Fix bug with rollups and slots.

1.0a6 (2015-10-21)
==================

- Allow dependencies of a Resources or a Group to be modified after
  being defined, but yet before being used. This allows to add
  optional dependencies then needed to generically defined
  packages. This required a complete re-factoring of the dependency
  mechanism.

- Fix slot so they can be used then a compiler is defined.

- Remove fanstatic.codegen. That was not applicable in enough cases.


1.0a5 (2014-02-09)
==================

- Fix issue #87 "install-error-with-python3":

  Fanstatic now depends on shutil.which when it's available
  (Python 3.3+) or uses shutilwhich library in other cases. This
  is useful because which.py is no longer supported.

  Thanks to Ivan Bulanov.

1.0a4 (2013-09-24)
==================

- Also setup the injector for HEAD requests. We don't want the app which we
  are wrapping to choke on the NotImplementedError raised by
  DummyNeededResources.

- Update entry points in order to use the fanstatic Publisher used as an
  application instead of a filter, for instance in a configuration
  with paste.urlmap.

  http://pythonpaste.org/modules/urlmap.html

1.0a3 (2013-08-12)
==================

- Refactor NeededResources into a pluggable injector system. Fanstatic users
  now have the possibility to customize how resources are injected into the
  HTML.

  We try to keep these changes backwards compatible for users that use
  the official API. People that use fanstatic internals are encouraged to
  update their code.

- Introduce "Inclusion" object; the responsibilities around bundling,
  compilation, debug/minified mode and rollup are moved from the
  NeededResources class to the Inclusion class.

1.0a2 (2013-05-25)
==================

- Move injection of the inclusions from the beginning of the <head> element to
  the end. See also:

  https://groups.google.com/forum/?fromgroups#!topic/fanstatic/VT_WasfDtL4

  This change may break your code, but it is probably a good idea to include
  the resources at the end of the <head>.

- Bugfix in sdist_compile: compile resources in *all* packages contained in a
  distribution.

- Fix tox/travis setup and update to buildout v2.

1.0a (2013-04-18)
=================

- Add support for compilers and minifiers.

  By default fanstatic ships with the sass/less and coffeescript compilers
  and mincss/minjs/google closure minifiers.

0.16 (2012-12-10)
=================

- Update Bundle object to share an API for the Resource one.

- Update injector to handle HTML pages that doesn't explicit set a
  charset in their headers.

0.15 (2012-11-08)
=================

- Add "default" argument to Slot to specify a resource which will be filled
  in if there is no other resource specified in need(). Thanks to nilo.

- Ensure published bundles carry the correct Content-Type header. Previously,
  all bundles were delivered with `text/html`. Thanks to David Beitey.


0.14 (2012-10-30)
=================

- Alex Grönholm added python3 and pypy support.

- Using tox to test on python2.6/2.7/3.2/3.3/pypy.

- Mirroring the bitbucket repo to github in order to run tests on travis-ci:

  https://travis-ci.org/#!/fanstatic/fanstatic

0.14a (2012-10-07)
==================

- Removed the dependency on Paste, replaced with webob.static.

- The publisher no longer sends out etags, which seems like a good
  idea. The `Yahoo best practices for speeding up web sites <http://developer.yahoo.com/performance/rules.html>`_
  say:

    If you're not taking advantage of the flexible validation model that
    ETags provide, it's better to just remove the ETag altogether.

- Updated package setup to be compatible with running
  ``python setup.py test``.

- Added tox setup for testing across python versions.

0.13.3 (2012-09-12)
===================

- No longer use WebOb's wsgify decorator in both the injector and
  delegator middlewares, as it has issues handling parent application
  WSGI response (https://github.com/Pylons/webob/issues/74).

0.13.2 (2012-08-23)
===================

- Fixed issue #78: "fanstatic.checksum.md5 is not guaranteed", thanks to
  takanao ENDOH.

0.13.1 (2012-08-16)
===================

- Fixed bug where mode resources created by string 'shortcut' didn't
  inherit the renderer, bundling, dependency parameters.

0.13 (2012-08-15)
=================

- DummyNeededResources did not takes the slots argument.

- Resource.need() did not process the slots argument, despite the argument
  being documented.

- Added slots argument to Group.need().


0.12 (2012-08-05)
=================

- Documentation fix in code samples, thanks to Toby Dacre.

- Fix issue #74, minified .js not served in bottom unless force_bottom,
  thanks to Toby Dacre.

- Cherry picked pull request #1 "support-wsgi-apps-not-mounted-at-/",
  thanks to Éric Lemoine.

- Add print css renderer.

0.11.4 (2012-01-14)
===================

- There was another bug with ordering resources when multiple libraries
  were involved. This time the way library_nr was calculated was changed
  so that it wouldn't happen anymore.

  The intent of library_nr was to have it always be 1 higher than the
  maximum library_nr of any libraries this library is based on.

  In practice this wouldn't always happen, because each resource had
  its own library_nr. In some circumstances the resources in libraries
  depending on other libraries would consistently get a library_nr too
  low, as each resource they were based on had a library_nr that was
  too low as well, even though another resource could exist in that
  library with a higher library_nr. This could cause the library_nr of
  all resources in a library to be too low.

  This is now fixed to moving library_nr to the place it should've
  maintained on in the first place: the library itself. It is
  calculated now once per library, just before the resources are
  sorted for the first time during the application's run. Since by the
  time resources need to be sorted all resources are known, the library_nr
  can be calculated correctly.

0.11.3 (2011-11-11)
===================

- There was a bug with ordering resources when multiple libraries
  are involved: https://bitbucket.org/fanstatic/fanstatic/issue/67/ordering-of-resources-when-multiple

0.11.2 (2011-05-19)
===================

- Update the docs for readthedocs.org.

0.11.1 (2011-04-13)
===================

- Consolidate the resources (find rollups) before applying the mode.

0.11 (2011-04-11)
=================

- Add bundling support: bundles are collections of Resources that can
  be served in one HTTP request. Bundle URLs are constructed by the
  fanstatic injector and served by the fanstatic publisher.

- Remove eager_superseder arguments from Resource, as this was not used.

- Abstracted features of Resource, Group, Bundle into base classes
  Renderable and Dependable.

- Improved sorting of resources for inclusion on web page. This is to
  prepare for bundling support. Ordering is now more consistent, no
  matter in which order resources are .needed(). As long as you marked
  dependencies right this shouldn't break applications; if your
  resources are included in the wrong order now, fix resource dependencies.

- base_url is not required anymore (as in the past); improve base_url
  management API so that integration packages like zope.fanstatic have
  a more explicit way to manage this information.

- Resources check whether the file they refer to exists or not. If
  the file doesn't exist you get an UnknownResourceError.

- Renamed UnknownResourceExtension exception to
  UnknownResourceExtensionError. The old exception name is still
  available for backwards compatibility.

- Use mtime instead of md5 for determining speeds up version computation
  during development. The hashing method is still available for people who
  don't trust their filesystem using the ``versioning_use_md5`` parameter.

0.10.1 (2011-02-06)
===================

- Fixed issue #49.


0.10 (2011-01-19)
=================

- Renamed ``hashing`` to ``versioning``. Use the version of the python package
  as the version identifier for a Library, unless the package is installed in
  development mode. If a Library has no version or is in development, use the
  hash of the Library's directory contents as version identifier.

- Consolidated the Resource modes into ``debug`` and ``minified``.

- The injector component only sets up the NeededResources if the request method
  is GET or POST.

- The ``devmode`` parameter has been renamed to ``recompute_hashes`` in order
  to more aptly reflect its behavior. When recompute_hashes is True, hashes are
  recomputed for every request - this is the default behavior.


0.9b (2011-01-06)
=================

Fanstatic is a fundamental rewrite of `hurry.resource`_. As such, Fanstatic
breaks compatibility with hurry.resource. Here's a list of essential changes
since version 0.10 of hurry.resource:

- Fundamental API cleanups and changes.

- Fanstatic no longer depends on ZTK packages, and provides several 'pure' WSGI
  components. This allows for greater re-use in different WSGI-based frameworks.

- `zope.fanstatic`_ (a rewrite of `hurry.zoperesource`_) provides the integration of
  Fanstatic with the ZTK.

- Fanstatic adds a WSGI component for serving resources, offloading it from the
  application framework.

- Fanstatic adds 'infinite' caching functionality by computing a unique URL
  for every version of a resource.

- Fanstatic uses `py.test`_ for test discovery and execution.

- A lot of effort has been put into documenting Fanstatic.

.. _`hurry.resource`: http://pypi.python.org/pypi/hurry.resource
.. _`hurry.zoperesource`: http://pypi.python.org/pypi/hurry.zoperesource
.. _`zope.fanstatic`: http://pypi.python.org/pypi/zope.fanstatic
.. _`py.test`: http://pypi.python.org/pypi/pytest
