from fanstatic import DEBUG, MINIFIED, compat

BOOL_CONFIG = set(['versioning', 'recompute_hashes', DEBUG, MINIFIED,
                   'bottom', 'force_bottom', 'bundle', 'rollup',
                   'versioning_use_md5', 'compile'])


# From paste.util.converters.
def asbool(obj):
    if isinstance(obj, compat.basestring):
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
    for key, value in compat.iteritems(config):
        if key in BOOL_CONFIG:
            result[key] = asbool(value)
        else:
            result[key] = value
    return result
