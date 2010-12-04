import inspect
import webob
import webob.dec
from paste.util.converters import asbool

import fanstatic

# TODO: would be nice to make middleware smarter so it could work with
# a streamed HTML body instead of serializing it out to body. That
# would complicate the middleware signicantly, however. We would for
# instance need to recalculate content_length ourselves.

class Inject(object):

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
    return Inject(app, **local_config)
