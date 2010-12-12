import webob
import webob.dec
from paste.util.converters import asbool

import fanstatic

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
    def __init__(self, app, **config):
        self.application = app

        # this is just to give useful feedback early on
        fanstatic.NeededResources(**config)
        
        self.config = config

    @webob.dec.wsgify
    def __call__(self, request):
        needed = fanstatic.init_needed(**self.config)

        # Get the response from the wrapped application:
        response = request.get_response(self.application)

        # We only continue if the content-type is appropriate.
        if not response.content_type.lower() in ['text/html', 'text/xml']:
            return response

        # The wrapped application may have left information in the environment
        # about needed resources
        if needed.has_resources():
            response.body = needed.render_topbottom_into_html(response.body)
        return response

def make_inject(app, global_config, **local_config):
    # XXX Sanitizing arguments might be factored out somehow. It is
    # duplicated in the make_fanstatic factory.
    devmode = local_config.get('devmode')
    if devmode is not None:
        local_config['devmode'] = asbool(devmode)
    rollup = local_config.get('rollup')
    if rollup is not None:
        local_config['rollup'] = asbool(rollup)
    bottom = local_config.get('bottom')
    if bottom is not None:
        local_config['bottom'] = asbool(bottom)
    return Injector(app, **local_config)
