import fanstatic

def Fanstatic(app, **config):
    # Wrap the app inside the inject middleware, inside the publisher
    # middleware.
    inject = fanstatic.Inject(app, **config)
    signature = config.get('publisher_signature', fanstatic.DEFAULT_SIGNATURE)
    return fanstatic.Delegator(inject, publisher_signature=signature)

def make_fanstatic(app, global_config, **local_config):
    return Fanstatic(**local_config)
