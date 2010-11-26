Concepts
========

To understand Fanstatic, we first need to get a few concepts straight.

Static resources are files that are used in the display of a web page,
such as CSS files, Javascript files and images. Often resources are
packaged as a collection of resources; we call this a *library* of
resources.

Resources can be included in a web page in several ways, by including
them on the web page. We call this a *resource inclusion*. The most
common way for Javascript and CSS is to include them in the ``head``
section of a HTML page. Javascript can also be included in script tags
elsewhere on the page, such as at the bottom. 

You can see an inclusion as a Python import: when you import a module,
you import a particular file in a particular package, and a resource
inclusion is the inclusion of a particular resource (``.js`` file,
``.css`` file) in a particular library. 

The most common forms of inclusion in HTML are Javascript files, which
are included using the ``script`` tag, for instance like this::

  <script type="text/javascript" src="/something.js"></script>

and CSS files, which are included using a ``link`` tag, like this::

  <link rel="stylesheet" href="/something.css" type="text/css" />

A resource inclusion may depend on other inclusions. A Javascript
resource may for instance require another Javascript resource. An
example of this is jQuery UI, which requires the inclusion of jQuery
on the page as well in order to work. 

Fanstatic takes care of inserting these inclusions on your web page
for you. It makes sure that inclusions with dependencies have their
dependencies loaded as well.

How do you tell Fanstatic that you'd like to include jQuery on a web
page? You do this by making an *inclusion requirement* in Python: you
state you *need* an inclusion.

It is common to construct complex web pages on the server with
cooperating components. A datetime widget may for instance expect a
particular datetime Javascript library to be loaded. Pages but also
sub-page components on the server may have inclusion requirements; you
can effectively make inclusion requirements anywhere on the server
side, as long as the code is executed somewhere during the request
that produces the page.
