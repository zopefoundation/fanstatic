Paste Deployment
================

.. py:module:: fanstatic

Fanstatic has support for `Paste Deployment`_, a system for
configuring WSGI applications and servers. You can configure the
Fanstatic WSGI components using Paste Deploy.

Fanstatic middleware
--------------------

Assuming you have configured you application with Paste, you will
already have a configuration ``.ini`` file, say ``deploy.ini``. You
can now wrap your application in the :py:func:`Fanstatic` middleware
like so::

  [server:main]
  use = egg:Paste#http

  [app:my_application]
  use = egg:myapplication

  [pipeline:main]
  pipeline = fanstatic my_application

  [filter:fanstatic]
  use = egg:fanstatic#fanstatic

The :py:func:`Fanstatic` middleware actually itself combines three
separate WSGI components - the :py:class:`Injector`, the
:py:class:`Delegator` and the :py:class:`Publisher` - into one
convient "package".

The ``[filter:fanstatic]`` section accepts several configuration
directives (see also the :doc:`Configuration documentation
<configuration>`):

Turn devmode on or off, accepts "true" or "false"::

  devmode = true

To turn on hashing, accepts "true" or "false"::

  hashing = true

The URL segment that is used in generating URLs to resources and to
recognize "serve-able" resource URLs::

  publisher_signature = foo

To allow for bottom inclusions, accepts "true" or "false"::

  bottom = true

To force *all* javascript to be bottom-included::

  force_bottom = true

Use this mode for the resource inclusions where available::

  mode = minified

Try to use rollup-ed resources where available::

  rollup = true

A complete ``[filter:fanstatic]`` section could look like this::

  [filter:fanstatic]
  use = egg:fanstatic#fanstatic
  devmode = false
  hashing = true
  bottom = true
  mode = minified

Injector middleware
-------------------

The :py:class:`Injector` WSGI component can be configured as a separate
middleware as well. This implies that the :py:class:`Injector` should
generate URLs that are served from elsewhere::

  [server:main]
  use = egg:Paste#http

  [app:my_application]
  use = egg:myapplication

  [pipeline:main]
  pipeline = injector my_application

  [filter:injector]
  use = egg:fanstatic#injector

The ``[filter:injector]`` section accepts the same set of
configuration parameters as the ``[filter:fanstatic`` section. A
complete section thus could look like this::

  [filter:injector]
  use = egg:fanstatic#injector
  devmode = false
  hashing = false
  bottom = true
  mode = minified

Publisher middleware
--------------------

The publisher middleware is actually a combination of a
:py:class:`Delegator` and a :py:class:`Publisher` component. The
delegator is responsible for recognizing what URLs are in fact URLs to
"serve-able" resources and what URLs should be handled by the wrapped
application.

URLs that contain the ``publisher_signature`` as a path segment are
recognized as "serve-able". Configuring only the publisher middleware
for you application, implies there is some other mechanism that
injects the correct resources URLs into, for example, web pages.

The publisher middleware accepts one configuration directive::

  [server:main]
  use = egg:Paste#http

  [app:my_application]
  use = egg:myapplication

  [pipeline:main]
  pipeline = publisher my_application

  [filter:publisher]
  use = egg:fanstatic#publisher
  publisher_signature = bar

Combining the publisher and the injector
----------------------------------------

As explained before, the :py:func:`Fanstatic` component combines the
publisher and injector middlewares. An equivalent configuration using
the separate components would look like this::

  [server:main]
  use = egg:Paste#http

  [app:my_application]
  use = egg:myapplication

  [pipeline:main]
  pipeline = publisher injector my_application

  [filter:publisher]
  use = egg:fanstatic#publisher
  publisher_signature = baz

  [filter:injector]
  use = egg:fanstatic#injector
  devmode = false
  hashing = true
  bottom = true
  mode = minified
  publisher_signature = baz

.. _`Paste Deployment`: http://pythonpaste.org/deploy/

