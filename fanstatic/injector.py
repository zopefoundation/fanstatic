import webob

from fanstatic.config import convert_config
from fanstatic import compat
import fanstatic
from fanstatic.core import Bundle

CONTENT_TYPES = ['text/html', 'text/xml', 'application/xhtml+xml']


class Injector(object):
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
        self.app = app

        # this is just to give useful feedback early on
        fanstatic.NeededResources(**config)

        self.config = config
        # BBB Backwards compatible: the default behavior was the top bottom
        # injector.
        if injector is None:
            injector = TopBottomInjector(config)
        self.injector = injector

    def __call__(self, environ, start_response):
        request = webob.Request(environ)
        # We only continue if the request method is appropriate.
        if not request.method in ['GET', 'POST']:
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


def bundle_resources(resources):
    """Bundle sorted resources together.

    resources is expected to be a list previously sorted by sorted_resources.

    Returns a list of renderable resources, which can include several
    resources bundled together into Bundles.
    """
    result = []
    bundle = Bundle()
    for resource in resources:
        if bundle.fits(resource):
            bundle.append(resource)
        else:
            # add the previous bundle to the list and create new bundle
            bundle.add_to_list(result)
            bundle = Bundle()
            if resource.dont_bundle:
                result.append(resource)
            else:
                bundle.append(resource)
    # add the last bundle to the list
    bundle.add_to_list(result)
    return result


class Inclusion(object):
    """Will be instantiated for every request."""

    def __init__(self, needed, resources=None, compile=False, bundle=False):
        # Needed is basically the context object.
        self.needed = needed
        if resources is None:
            resources = needed.resources()
        self.resources = resources
        if compile:
            for resource in self.resources:
                resource.compile()
        if bundle:
            self.resources = bundle_resources(resources)

    def __len__(self):
        return len(self.resources)

    def render(self):
        result = []
        for resource in self.resources:
            result.append(
                resource.render(
                    self.needed.library_url(resource.library)))
        return '\n'.join(result)


class TopBottomInjector(object):

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

        :param bundle: If set to True, Fanstatic will attempt to bundle
          resources that fit together into larger Bundle objects. These
          can then be rendered as single URLs to these bundles.

        :param compile: XXX
        """

        self._bottom = options.pop('bottom', False)
        self._force_bottom = options.pop('force_bottom', False)
        self._compile = options.pop('compile', False)
        self._bundle = options.pop('bundle', False)

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
            Inclusion(needed,
                top_resources, compile=self._compile, bundle=self._bundle),
            Inclusion(needed,
                bottom_resources, compile=self._compile, bundle=self._bundle)
        )

    def __call__(self, html, needed, request=None, response=None):
        # seperate inclusions in top and bottom inclusions if this is needed
        top, bottom = self.group(needed)
        if top:
            html = html.replace(
                compat.as_bytestring('</head>'),
                compat.as_bytestring('%s</head>' % top.render()), 1)
        if bottom:
            html = html.replace(
                compat.as_bytestring('</body>'),
                compat.as_bytestring('%s</body>' % bottom.render()), 1)
        return html


def make_injector(app, global_config, **local_config):
    local_config = convert_config(local_config)
    # Look up injector factory by name.
    injector_name = local_config.get('injector', 'topbottom')
    injector_factory = fanstatic.registry.InjectorRegistry.instance().get(injector_name)
    if injector_factory is None:
        raise ConfigurationError('No injector found for name %s' % injector_name)
    injector = injector_factory(local_config)
    return Injector(app, **local_config)
