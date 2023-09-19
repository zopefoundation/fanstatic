import webob

import fanstatic
from fanstatic import DEBUG
from fanstatic import MINIFIED
from fanstatic import ConfigurationError
from fanstatic.config import convert_config
from fanstatic.inclusion import Inclusion


CONTENT_TYPES = ['text/html', 'text/xml', 'application/xhtml+xml']


class Injector:
    """Fanstatic injector WSGI framework component.

    This WSGI component takes care of injecting the proper resource
    inclusions into HTML when needed.

    This WSGI component is used automatically by the
    :py:func:`Fanstatic` WSGI framework component, but can also be
    used independently if you need more control.

    :param app: The WSGI app to wrap with the injector.

    :param ``**config``: Optional keyword arguments. These are passed
      to :py:class:`NeededResources` when it is constructed. It also
      makes sure that when initialized, it isn't given any
      configuration parameters that cannot be passed to
      ``NeededResources``.
    """

    def __init__(self, app, injector=None, **config):
        # BBB Backwards compatible: the default behavior was the top
        # bottom injector. It need to be called first since it will
        # remove options from config.
        if injector is None:
            injector = TopBottomInjector(config)

        # This is just to validate config
        fanstatic.NeededResources(**config)

        self.app = app
        self.config = config
        self.injector = injector

    def __call__(self, environ, start_response):
        request = webob.Request(environ)
        # We only continue if the request method is appropriate.
        if request.method not in ['GET', 'POST', 'HEAD']:
            return self.app(environ, start_response)

        # Initialize a needed resources object.
        # XXX this will set the needed on the thread local data, even
        # if the wrapped framework only gets the needed from the WSGI
        # environ.
        needed = fanstatic.init_needed(
            script_name=request.environ.get('SCRIPT_NAME'), **self.config)

        # Make sure the needed resource object is put in the WSGI
        # environment as well, for frameworks that choose to use it
        # from there.
        request.environ[fanstatic.NEEDED] = needed

        # Get the response from the wrapped application:
        response = request.get_response(self.app)
        # We only continue if the content-type is appropriate.
        if not (response.content_type and
                response.content_type.lower() in CONTENT_TYPES):
            # Clean up after our behinds.
            fanstatic.del_needed()
            return response(environ, start_response)

        # The wrapped application may have `needed` resources.
        if needed.has_resources():
            # Can't use response.text because there might not be any
            # charset. body is not unicode.
            result = self.injector(response.body, needed, request, response)
            # Reset the body...
            response.body = b''
            # Write will propely unfolder the previous application and
            # call close. Setting response.text or response.body won't do it.
            response.write(result)

        # Clean up after our behinds.
        fanstatic.del_needed()

        return response(environ, start_response)


class InjectorPlugin:
    """Base class that can be use to write an injector plugin. It will
    take out from the configuration the common options that can be
    used in conjunction with an Inclusion.
    """

    def __init__(self, options):
        self._compile = options.pop('compile', False)
        self._bundle = options.pop('bundle', False)
        self._rollup = options.pop('rollup', False)
        debug = options.pop('debug', False)
        minified = options.pop('minified', False)
        self._mode = None
        if (debug and minified):
            raise ConfigurationError('Choose *one* of debug and minified')
        if debug is True:
            self._mode = DEBUG
        if minified is True:
            self._mode = MINIFIED

    def make_inclusion(self, needed, resources=None):
        """Helper to create an Inclusion passing all the options
        configured in the configuration file.
        """
        return Inclusion(
            needed, resources=resources,
            compile=self._compile, bundle=self._bundle,
            mode=self._mode, rollup=self._rollup)

    def __call__(self, html, needed, request=None, response=None):
        """ Render the needed resources into the html.
        The request and response arguments are
        webob Request and Response objects.
        """
        raise NotImplementedError


class TopBottomInjector(InjectorPlugin):

    name = 'topbottom'

    def __init__(self, options):
        """
        :param bottom: If set to ``True``, Fanstatic will include any
          resource that has been marked as "bottom safe" at the bottom of
          the web page, at the end of ``<body>``, as opposed to in the
          ``<head>`` section. This is useful for optimizing the load-time
          of Javascript resources.

        :param force_bottom: If set to ``True`` and ``bottom`` is set to
          ``True`` as well, all Javascript resources will be included at
          the bottom of a web page, even if they aren't marked bottom
          safe.

        """
        super().__init__(options)
        self._bottom = options.pop('bottom', False)
        self._force_bottom = options.pop('force_bottom', False)

    def group(self, needed):
        """Return the top and bottom resources."""
        resources = needed.resources()
        if self._bottom:
            top_resources = []
            bottom_resources = []
            if not self._force_bottom:
                for resource in resources:
                    if resource.bottom:
                        bottom_resources.append(resource)
                    else:
                        top_resources.append(resource)
            else:
                for resource in resources:
                    if resource.ext == '.js':
                        bottom_resources.append(resource)
                    else:
                        top_resources.append(resource)
        else:
            top_resources = resources
            bottom_resources = []
        return (
            self.make_inclusion(needed, top_resources),
            self.make_inclusion(needed, bottom_resources)
        )

    def __call__(self, html, needed, request=None, response=None):
        # seperate inclusions in top and bottom inclusions if this is needed
        top, bottom = self.group(needed)
        if top:
            html = html.replace(
                b'</head>', f'{top.render()}</head>'.encode(), 1)
        if bottom:
            html = html.replace(
                b'</body>', f'{bottom.render()}</body>'.encode(), 1)
        return html


def make_injector(app, global_config, **local_config):
    local_config = convert_config(local_config)
    # Look up injector factory by name.
    injector_name = local_config.pop('injector', 'topbottom')
    injector_factory = fanstatic.registry.InjectorRegistry.instance().get(
        injector_name)
    if injector_factory is None:
        raise ConfigurationError(
            'No injector found for name %s' % injector_name)
    injector = injector_factory(local_config)
    return Injector(app, injector=injector, **local_config)
