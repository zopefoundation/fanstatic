import inspect
import webob
import webob.dec
from paste.util.converters import asbool

import fanstatic

class Injector(object):
    """Fanstatic injector WSGI framework component.

    This WSGI component takes care of injecting the proper inclusions
    into HTML when needed.

    This WSGI component is used automatically by the
    :py:func:`Fanstatic` WSGI framework component, but can also be
    used independently if you need more control.
    
    :param app: The WSGI app to wrap with the injector.

    :param ``**config``: Optional keyword arguments. These are
      passed to :py:class:`NeededInclusions` when it is constructed.
    """
    def __init__(self, app, **config):
        self.application = app

        self._check_inclusions_signature(**config)
        self.config = config

    # To get a correct error message on initialize-time, we construct
    # a function that has the same signature as NeededInclusions(),
    # but without "self".
    def _check_inclusions_signature(self, **config):
        args, varargs, varkw, defaults = inspect.getargspec(
            fanstatic.NeededInclusions.__init__)
        argspec = inspect.formatargspec(args[1:], varargs, varkw, defaults)
        exec("def signature_checker" + argspec + ": pass")
        try:
            signature_checker(**config)
        except TypeError, e:
            message = e.args[0]
            message = message.replace(
                "signature_checker()", fanstatic.NeededInclusions.__name__)
            raise TypeError(message)

    @webob.dec.wsgify
    def __call__(self, request):
        needed = fanstatic.init_current_needed_inclusions(**self.config)

        # Get the response from the wrapped application:
        response = request.get_response(self.application)

        # We only continue if the content-type is appropriate.
        if not response.content_type.lower() in ['text/html', 'text/xml']:
            return response

        # The wrapped application may have left information in the environment
        # about needed inclusions.
        if needed.has_inclusions():
            response.body = needed.render_topbottom_into_html(response.body)
        return response

def make_inject(app, global_config, **local_config):
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
