Paste Deployment
================

.. py:module:: fanstatic

Fanstatic has support for `Paste Deployment`_, a system for
configuring WSGI applications and servers. You can configure the
Fanstatic WSGI components using Paste Deploy.

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

  publisher_signature = stanfatic

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

.. _`Paste Deployment`: http://pythonpaste.org/deploy/

