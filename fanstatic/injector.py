import webob
import webob.dec

from fanstatic.config import convert_config
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
        self.app = app

        # this is just to give useful feedback early on
        fanstatic.NeededResources(**config)
        
        self.config = config

    @webob.dec.wsgify
    def __call__(self, request):
        needed = fanstatic.init_needed(**self.config)

        # Get the response from the wrapped application:
        response = request.get_response(self.app)

        # We only continue if the content-type is appropriate.
        if not response.content_type.lower() in ['text/html', 'text/xml']:
            return response

        # The wrapped application may have left information in the environment
        # about needed resources
        if needed.has_resources():
            response.body = needed.render_topbottom_into_html(response.body)
        return response

def make_injector(app, global_config, **local_config):
    local_config = convert_config(local_config)
    return Injector(app, **local_config)
