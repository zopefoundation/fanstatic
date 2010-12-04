API Overview
============

Inclusion renderers
===================

The HTML fragments for inclusions are rendered by ``inclusion renderers``
that are simple functions registered per extension.

Renderers are registered in the ``inclusion_renderers`` dictionary:

  >>> from hurry.resource.core import inclusion_renderers
  >>> sorted(inclusion_renderers)
  ['.css', '.js', '.kss']

Renderers render HTML fragments using given resource URL:

  >>> inclusion_renderers['.js']('http://localhost/script.js')
  '<script type="text/javascript" src="http://localhost/script.js"></script>'

Let's create an inclusion of unknown resource:

  >>> a6 = ResourceInclusion(foo, 'nothing.unknown')
  >>> from hurry.resource.core import EXTENSIONS
  >>> EXTENSIONS.append('.unknown')

  >>> needed = NeededInclusions()
  >>> needed.base_url = 'http://localhost/static/'
  >>> needed.need(a6)
  >>> needed.render()
  Traceback (most recent call last):
  ...
  UnknownResourceExtension: Unknown resource extension .unknown for resource
                            inclusion: <ResourceInclusion 'nothing.unknown'
                            in library 'foo'>

Now let's add a renderer for our ".unknown" extension and try again:

  >>> def render_unknown(url):
  ...     return '<link rel="unknown" href="%s" />' % url
  >>> inclusion_renderers['.unknown'] = render_unknown
  >>> needed.render()
  '<link rel="unknown" href="http://localhost/static/fanstatic/:hash:.../foo/nothing.unknown" />'

