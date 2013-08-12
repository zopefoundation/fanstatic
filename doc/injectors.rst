Injector plugins
================

Fanstatic allows you to write your own injector plugins. Injector plugins take
care of injecting the needed resources into the HTML of the response.

The default injector plugin is the "TopBottomInjector", which injects
resources into the top (the head section) and bottom (before the closing body
tag) of the page.

To write your own injector plugin, you need to do the following::

  from fanstatic.injector import InjectorPlugin

  class MyInjector(InjectorPlugin):

      name = 'mine'

      def __init__(self, options):
          """Optionally, you can control the configuration of the injector
          plugin here. The options are taken from the local_conf of the paste
          deploy configuration. Don't forget to super()."""

      def __call__(self, html, needed, request=None, response=None):
          """Render the needed resources into the html.
             The request and response arguments are
             webob Request and Response objects that may be relevant for how
             you want to inject the resources.

             You may want to group the resources in the needed resources.
             For every group call self.make_inclusion(), which will return an
             Inclusion object. Calling render() on an Inclusion object,
             will return an html snippet, which you can then include in the
             html.
          """
          needed_html = self.make_inclusion(needed).render()
          return html.replace('<head>', '<head>%s' % needed_html, 1)

After writing the plugin code, register the plugin through the
"fanstatic.injectors" entry point.

An example of an injector plugin with configuration taken from paste deploy
can be found in the sylva.fanstatic_ package.

.. _sylva.fanstatic: http://silvacms.org/getsilva/packages/silva_all/silva.fanstatic
