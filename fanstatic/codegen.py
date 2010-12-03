from fanstatic import sort_inclusions_topological, sort_inclusions_by_extension

def generate_code(**kw):
    name_to_inclusion = kw
    inclusion_to_name = {}
    inclusions = []
    for name, inclusion in kw.items():
        inclusion_to_name[inclusion.key()] = name
        inclusions.append(inclusion)

    # libraries with the same name are the same libraries
    libraries = {}
    for inclusion in inclusions:
        libraries[inclusion.library.name] = inclusion.library
    libraries = sorted(libraries.values())

    result = []
    # import on top
    result.append("from fanstatic import Library, ResourceInclusion")
    result.append("")
    # define libraries
    for library in libraries:
        result.append("%s = Library('%s', '%s')" %
                      (library.name, library.name, library.rootpath))
    result.append("")

    # sort inclusions in the order we want them to be
    inclusions = sort_inclusions_by_extension(
        sort_inclusions_topological(inclusions))

    # now generate inclusion code
    for inclusion in inclusions:
        s = "%s = ResourceInclusion(%s, '%s'" % (
            inclusion_to_name[inclusion.key()],
            inclusion.library.name,
            inclusion.relpath)
        if inclusion.depends:
            depends_s = ', depends=[%s]' % ', '.join(
                [inclusion_to_name[d.key()] for d in inclusion.depends])
            s += depends_s
        if inclusion.supersedes:
            supersedes_s = ', supersedes=[%s]' % ', '.join(
                [inclusion_to_name[i.key()] for i in inclusion.supersedes])
            s += supersedes_s
        if inclusion.modes:
            items = []
            for mode_name, mode in inclusion.modes.items():
                items.append((mode_name,
                              generate_inline_inclusion(mode, inclusion)))
            items = sorted(items)
            modes_s = ', %s' % ', '.join(["%s=%s" % (name, mode) for
                                          (name, mode) in items])
            s += modes_s
        s += ')'
        result.append(s)
    return '\n'.join(result)

def generate_inline_inclusion(inclusion, associated_inclusion):
    if inclusion.library.name == associated_inclusion.library.name:
        return "'%s'" % inclusion.relpath
    else:
        return "ResourceInclusion(%s, '%s')" % (inclusion.library.name,
                                                inclusion.relpath)

