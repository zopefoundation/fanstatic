from paste.util.converters import asbool

BOOL_CONFIG = set(['hashing', 'devmode', 'bottom', 'force_bottom', 'rollup'])

def convert_config(config):
    result = {}
    for key, value in config.items():
        if key in BOOL_CONFIG:
            result[key] = asbool(value)
        else:
            result[key] = value
    return result
