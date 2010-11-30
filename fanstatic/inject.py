import webob
from paste.util.converters import asbool

import fanstatic

# TODO: would be nice to make middleware smarter so it could work with
# a streamed HTML body instead of serializing it out to body. That
# would complicate the middleware signicantly, however. We would for
# instance need to recalculate content_length ourselves.

class Inject(object):

    def __init__(self, application, **config):
        self.application = application
        self.config = config

    def __call__(self, environ, start_response):
        needed = fanstatic.init_current_needed_inclusions(**self.config)

        # Get the response from the wrapped application:
        request = webob.Request(environ)
        response = request.get_response(self.application)

        # Post-process the response:
        # We only continue if the content-type is appropriate.
        if not response.content_type.lower() in ['text/html', 'text/xml']:
            return response(environ, start_response)

        # The wrapped application may have left information in the environment
        # about needed inclusions.
        if len(needed):
            response.body = needed.render_topbottom_into_html(response.body)
        return response(environ, start_response)

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
