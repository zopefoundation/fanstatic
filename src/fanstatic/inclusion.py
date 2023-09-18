from fanstatic.core import Bundle


def bundle_resources(resources):
    """Bundle sorted resources together.

    resources is expected to be a list previously sorted by sorted_resources.

    Returns a list of renderable resources, which can include several
    resources bundled together into Bundles.
    """
    result = []
    bundle = Bundle()
    for resource in resources:
        if bundle.fits(resource):
            bundle.append(resource)
        else:
            # add the previous bundle to the list and create new bundle
            bundle.add_to_list(result)
            bundle = Bundle()
            if resource.dont_bundle:
                result.append(resource)
            else:
                bundle.append(resource)
    # add the last bundle to the list
    bundle.add_to_list(result)
    return result


def rollup_resources(resources):
    """Rollup resources together: if a resource include multiple
    separate ones (i.e. is a rollup) and all the separate ones are
    included the rollup will be used instead.
    """
    # keep track of rollups: rollup key -> set of resource keys
    potential_rollups = {}
    for resource in resources:
        for rollup in resource.rollups:
            s = potential_rollups.setdefault(
                (rollup.library, rollup.relpath), set())
            s.add((resource.library, resource.relpath))

    # now go through resources, replacing them with rollups if
    # conditions match
    result = set()
    for resource in resources:
        superseders = []
        for rollup in resource.rollups:
            s = potential_rollups[(rollup.library, rollup.relpath)]
            if len(s) == len(rollup.supersedes):
                superseders.append(rollup)
        if superseders:
            # use the exact superseder that rolls up the most
            superseders = sorted(superseders, key=lambda i: len(i.supersedes))
            result.add(superseders[-1])
        else:
            # nothing to supersede resource so use it directly
            result.add(resource)
    return result


def sort_resources(resources):
    """Sort resources for inclusion on web page.

    A number of rules are followed:

    * resources are always grouped per renderer (.js, .css, etc)
    * resources that depend on other resources are sorted later
    * resources are grouped by library, if the dependencies allow it
    * libraries are sorted by name, if dependencies allow it
    * resources are sorted by resource path if they both would be
      sorted the same otherwise.

    The only purpose of sorting on library is so we can
    group resources per library, so that bundles can later be created
    of them if bundling support is enabled.

    Note this sorting algorithm guarantees a consistent ordering, no
    matter in what order resources were needed.
    """
    def key(resource):
        return (
            resource.order,
            resource.library.library_nr,
            resource.library.name,
            resource.dependency_nr,
            resource.relpath)
    return sorted(resources, key=key)


class Inclusion:
    """
    An Inclusion is a container/group for a set of Resources that are needed.
    The Inclusion controls various aspects of these Resources:

    :param mode: If set to ``MINIFIED``, Fanstatic will include all
      resources in ``minified`` form. If a Resource instance does not
      provide a ``minified`` mode, the "main" (non-named) mode is used.

      If set to ``DEBUG``, Fanstatic will include all
      resources in ``debug`` form. If a Resource instance does not
      provide a ``debug`` mode, the "main" (non-named) mode is used.
      An exception is raised when both the ``debug`` and ``minified``
      parameters are ``True``.

    :param rollup: If set to True (default is False) rolled up
      combined resources will be served if they exist and supersede
      existing resources that are needed.

    :param bundle: If set to True, Fanstatic will attempt to bundle
      resources that fit together into larger Bundle objects. These
      can then be rendered as single URLs to these bundles.

    :param compile: If set to True, Fanstatic will compile resources
      for every time the Inclusion is created. You'll probably want to set
      this to False in a production environment.
    """

    def __init__(
            self, needed, resources=None,
            compile=False, bundle=False,
            mode=None, rollup=False):
        # Needed is basically the context object.
        self.needed = needed

        if resources is None:
            resources = needed.resources()

        if rollup:
            resources = rollup_resources(resources)

        if mode is not None:
            resources = [resource.mode(mode) for resource in resources]

        resources = sort_resources(resources)

        if compile:
            for resource in resources:
                resource.compile()

        if bundle:
            resources = bundle_resources(resources)

        self.resources = resources

    def __len__(self):
        return len(self.resources)

    def render(self):
        result = []
        for resource in self.resources:
            result.append(
                resource.render(
                    self.needed.library_url(resource.library)))
        return '\n'.join(result)
