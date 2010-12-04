Fanstatic Quickstart
====================

This quickstart will demonstrate how to integrate Fanstatic into a very
simple web application.

A simple WSGI application here will stand in for your web
application. In this example, we will use Python to hook up Fanstatic
to the WSGI application, but you could also use a WSGI configuration
framework like `Paste Deploy`_.

.. _`Paste Deploy`: http://pythonpaste.org/deploy/

This is our application::

    def app(environ, start_response):
        start_response('200 OK', [])
        return ['<html><head></head><body</body></html>']

As you can see, it simply produces the following web page::

  <html><head></head><body</body></html>

Let's say we want to start using jQuery in this application. The way
to do this without Fanstatic would be:

* download jQuery somewhere and install it into your web server, or
  alternatively use a URL to jQuery already published somewhere on the
  web using a content distribution network (CDN).

* modify the ``<head>`` section of the HTML in your code to add a
  ``<script>`` tag that references jQuery, in all HTML pages that need
  jQuery.

This is fine for simple requirements, but gets hairy once you have a
lot of pages that need a variety of Javascript libraries (which may
change dynamically), or if you need a larger selection of Javascript
libraries with a more involved dependency structure. Soon you find
yourself juggling HTML templates with lots of ``<script>`` tags,
puzzling over what depends on what, and organizing a large variety of
static resources.

How would we do this with Fanstatic? Like this::

    from js.jquery import jquery

    def app(environ, start_response):
        start_response('200 OK', [])
        jquery.need()
        return ['<html><head></head><body</body></html>']

You also need to make sure that ``js.jquery`` is available in your
project using a familiar Python library installation system such as
pip, easy_install or buildout. This will automatically make the
Javascript code available on your system.

You also need to configure your application so that Fanstatic can do two
things for you:

* automatically inject resource
  inclusion requirements (the ``<script>`` tag) into your web page.

* serve the static resources (such as jQuery.js) when a request to a
  resource is made.

Fanstatic provides a WSGI framework component called ``Fanstatic``
that does both of these things for you. Here is how you use it::

  from fanstatic import Fanstatic
  
  fanstatic_app = Fanstatic(app)

When you use ``fanstatic_app``, Fanstatic will take of serving static
resources for you, and includes them on web pages when needed. You can
import and ``need`` resources all through your application's code, and
Fanstatic will make sure that they are served correctly and that the
right script tags appear on your web page.

Now you're off and running with Fanstatic!
