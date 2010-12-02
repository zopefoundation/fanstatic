from paste.util.converters import asbool

import fanstatic

def Fanstatic(app, **config):
    # Wrap the app inside the inject middleware, inside the publisher
    # middleware.
    inject = fanstatic.Inject(app, **config)
    signature = config.get('publisher_signature', fanstatic.DEFAULT_SIGNATURE)
    return fanstatic.Delegator(inject, publisher_signature=signature)

def make_fanstatic(app, global_config, **local_config):
    devmode = local_config.get('devmode')
    if devmode is not None:
        local_config['devmode'] = asbool(devmode)
    rollup = local_config.get('rollup')
    if rollup is not None:
        local_config['rollup'] = asbool(rollup)
    bottom = local_config.get('bottom')
    if bottom is not None:
        local_config['bottom'] = asbool(bottom)
    return Fanstatic(app, **local_config)
