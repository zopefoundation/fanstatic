Integration
===========

Fanstatic can be integrated with a number of web frameworks:

* Zope/Grok through `zope.fanstatic <https://pypi.org/project/zope.fanstatic>`_

* Pyramid through `pyramid_fanstatic <https://pypi.org/project/pyramid_fanstatic>`_

* Flask through `Flask-Fanstatic <https://pypi.org/project/Flask-Fanstatic>`_

* Django through django_fanstatic_.

.. _django_fanstatic: https://github.com/fanstatic/django-fanstatic

In order to integrate Fanstatic with your web framework, make sure the
following conditions are met:

* **base_url**: if your web framework supports virtual hosting, make sure
  to set the ``base_url`` attribute on the ``NeededResources`` object.

* **Error pages**: if your web framework renders error pages, make sure to
  clear the ``NeededResources`` before rendering the error page, in order to
  prevent resources from the original page 'leaking' onto the error page.

* **URL calculation**: Fanstatic can also serve non-JavaScript and non-CSS
  resources (such as images) that you link to from the views in your
  application.  In order to do so, we advise to support rendering URLs to
  resources from the view/page templates in your web framework.
