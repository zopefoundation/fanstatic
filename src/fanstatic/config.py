from fanstatic import DEBUG
from fanstatic import MINIFIED


BOOL_CONFIG = {'versioning', 'recompute_hashes', DEBUG, MINIFIED,
               'bottom', 'force_bottom', 'bundle', 'rollup',
               'versioning_use_md5', 'compile'}


# From paste.util.converters.
def asbool(obj):
    if isinstance(obj, str):
        obj = obj.strip().lower()
        if obj in ['true', 'yes', 'on', 'y', 't', '1']:
            return True
        elif obj in ['false', 'no', 'off', 'n', 'f', '0']:
            return False
        else:
            raise ValueError(
                "String is not true/false: %r" % obj)
    return bool(obj)


def convert_config(config):
    result = {}
    for key, value in config.items():
        if key in BOOL_CONFIG:
            result[key] = asbool(value)
        else:
            result[key] = value
    return result
