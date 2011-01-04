from fanstatic import sort_resources_topological, sort_resources

def generate_code(**kw):
    resource_to_name = {}
    resources = []
    for name, resource in kw.items():
        resource_to_name[resource.key()] = name
        resources.append(resource)

    # libraries with the same name are the same libraries
    libraries = {}
    for resource in resources:
        libraries[resource.library.name] = resource.library
        for mode_name, mode_resource in resource.modes.items():
            libraries[mode_resource.library.name] = mode_resource.library
    libraries = sorted(libraries.values(), key=lambda library: library.name)

    result = []
    # import on top
    result.append("from fanstatic import Library, Resource")
    result.append("")
    # define libraries
    for library in libraries:
        result.append("%s = Library('%s', '%s')" %
                      (library.name, library.name, library.rootpath))
    result.append("")

    # sort resources in the order we want them to be
    resources = sort_resources(
        sort_resources_topological(resources))

    # now generate resource code
    for resource in resources:
        s = "%s = Resource(%s, '%s'" % (
            resource_to_name[resource.key()],
            resource.library.name,
            resource.relpath)
        if resource.depends:
            depends_s = ', depends=[%s]' % ', '.join(
                [resource_to_name[d.key()] for d in resource.depends])
            s += depends_s
        if resource.supersedes:
            supersedes_s = ', supersedes=[%s]' % ', '.join(
                [resource_to_name[i.key()] for i in resource.supersedes])
            s += supersedes_s
        if resource.modes:
            items = []
            for mode_name, mode in resource.modes.items():
                items.append((mode_name,
                              generate_inline_resource(mode, resource)))
            items = sorted(items)
            modes_s = ', %s' % ', '.join(["%s=%s" % (name, mode) for
                                          (name, mode) in items])
            s += modes_s
        s += ')'
        result.append(s)
    return '\n'.join(result)

def generate_inline_resource(resource, associated_resource):
    if resource.library.name == associated_resource.library.name:
        return "'%s'" % resource.relpath
    else:
        return "Resource(%s, '%s')" % (resource.library.name,
                                       resource.relpath)

