from paste.util.converters import asbool

import fanstatic
from fanstatic import Inject, Delegator, Publisher, library_registry

def Fanstatic(app, **config):
    # wrap the app inside the inject middleware, inside the publisher
    # middleware.
    signature = config.get('publisher_signature', fanstatic.DEFAULT_SIGNATURE)
    return Delegator(Inject(app, **config),
                     Publisher(library_registry.values()),
                     publisher_signature=signature)

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
