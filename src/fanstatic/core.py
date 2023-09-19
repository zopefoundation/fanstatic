import os
import sys
import threading

import fanstatic.checksum
import fanstatic.registry


DEFAULT_SIGNATURE = 'fanstatic'

VERSION_PREFIX = ':version:'

BUNDLE_PREFIX = ':bundle:'

NEEDED = 'fanstatic.needed'

DEBUG = 'debug'
MINIFIED = 'minified'

_resource_file_existence_checking = True
_auto_register_library = False


def set_resource_file_existence_checking(v):
    """Set resource file existence checking to True or False.

    By default, this is set to True, so that resources that point to
    non-existent files will result in an error. We recommend you keep
    it at this value when using Fanstatic. An
    :py:class:`UnknownResourceError` will then be raised if you
    accidentally refer to a non-existent resource.

    When running tests it's often useful to make fake resources that
    don't really have a filesystem representation, so this is set to
    False temporarily; for the Fanstatic tests this is done. Inside
    a test for this particular feature, this can temporarily be set
    to True.
    """
    global _resource_file_existence_checking
    _resource_file_existence_checking = v


def set_auto_register_library(v):
    """
    Global to say whether the Library instances should auto-register
    themselves to the Library registry. Defaults to False, is useful in tests.
    """
    global _auto_register_library
    _auto_register_library = v


class UnknownResourceExtensionError(Exception):
    """A resource has an unrecognized extension.
    """


class ModeResourceDependencyError(Exception):
    """A Mode Resource does not have the same dependencies as the
    resource it replaces.
    """


# BBB backwards compatibility
UnknownResourceExtension = UnknownResourceExtensionError


class UnknownResourceError(Exception):
    """Resource refers to non-existent resource file.
    """


class ConfigurationError(Exception):
    """Impossible or illegal configuration.
    """


class LibraryDependencyCycleError(Exception):
    """Dependency cycles between libraries aren't allowed.

    A dependency cycle between libraries occurs when the file in one
    library depends on a file in another library, while that library
    depends on a file in the first library.
    """


class SlotError(Exception):
    """A slot was filled in incorrectly.

    If a slot is required, it must be filled in by passing an extra
    dictionary parameter to the ``.need`` method, containing a mapping
    from the required :py:class:`Slot` to :py:class:`Resource`.

    When a slot is filled, the resource filled in should have
    the same dependencies as the slot, or a subset of the dependencies
    of the slot. It should also have the same extension as the slot.
    If this is not the case, it is an error.
    """


class Library:
    """The resource library.

    This object defines which directory is published and can be
    referred to by :py:class:`Resource` objects to describe
    these resources.

    :param name: A string that uniquely identifies this library.

    :param rootpath: An absolute or relative path to the directory
      that contains the static resources this library publishes. If
      relative, it will be relative to the directory of the module
      that initializes the library.

    :param ignores: A list of globs used to determine which files
      and directories not to publish.
    """

    path = None
    """
    The absolute path to the directory which contains the static resources
    this library publishes.
    """

    _signature = None

    def __init__(self, name, rootpath, ignores=None, version=None,
                 compilers=None, minifiers=None):
        self.name = name
        self.rootpath = rootpath
        self.ignores = ignores or []
        self.path = os.path.join(caller_dir(), rootpath)
        self.version = version
        self._library_deps = set()
        self.known_resources = {}
        self.known_assets = []
        self.library_nr = None
        self.module = sys._getframe(1).f_globals['__name__']

        self.compilers = compilers
        if self.compilers is None:
            self.compilers = {}
        self.minifiers = minifiers
        if self.minifiers is None:
            self.minifiers = {}

        if _auto_register_library:
            fanstatic.get_library_registry().add(self)

    def __repr__(self):
        return "<Library '{}' at '{}'>".format(self.name, self.path)

    def init_library_nr(self):
        """This can only be called once all resources are known.

        i.e. once sort_resources is called this can be called.
        once library numbers are calculated once this will be done
        very quickly.
        """
        # if there already is a known library nr, we're done
        if self.library_nr is not None:
            return
        # the maximum library number is the maximum number of the
        # depending libraries + 1
        max_library_nr = 0
        for resource in self.known_resources.values():
            for depend in resource.depends:
                for asset in depend.list_assets():
                    # we don't care about resources in the same library
                    if asset.library is self:
                        continue
                    # assign library number of library we are dependent on
                    # recursively if necessary
                    if asset.library.library_nr is None:
                        asset.library.init_library_nr()
                    max_library_nr = max(
                        max_library_nr, asset.library.library_nr + 1)
        self.library_nr = max_library_nr

    def check_dependency_cycle(self, resource):
        for dependency in resource.resources:
            self._library_deps.add(dependency.library)
        for dep in self._library_deps:
            if dep is self:
                continue
            if self in dep._library_deps:
                raise LibraryDependencyCycleError(
                    'Library cycle detected in resource %s' % resource)

    def register(self, resource):
        """Register a Resource with this Library.

        A Resource knows about its Library. After a Resource has registered
        itself with its Library, the Library knows about the Resources
        associated to it.
        """
        if isinstance(resource, Resource):
            if resource.relpath in self.known_resources:
                raise ConfigurationError(
                    'Resource path %s is already defined.' % resource.relpath)
            self.known_resources[resource.relpath] = resource
        self.known_assets.append(resource)

    def signature(self, recompute_hashes=False, version_method=None):
        """Get a unique signature for this Library.

        If a version has been defined, we return the version.

        If no version is defined, a hash of the contents of the directory
        indicated by ``path`` is calculated.
        If ``recompute_hashes`` is set to ``True``, the signature will be
        recalculated each time, which is useful during development when
        changing Javascript/css code and images.
        """
        if self.version is not None:
            return VERSION_PREFIX + self.version

        if recompute_hashes:
            # Always re-compute.
            sig = version_method(self.path)
        elif self._signature is None:
            # Only compute if not computed before.
            sig = self._signature = version_method(self.path)
        else:
            # Use cached value.
            sig = self._signature
        return VERSION_PREFIX + sig


# Total hack to be able to get the dir the resources will be in.
def caller_dir():
    return os.path.dirname(sys._getframe(2).f_globals['__file__'])


class InclusionRenderers(dict):

    _default_order = 0

    def register(self, extension, renderer, order=None):
        """Register a renderer function for a given filename extension.

        :param extension: the filename extension to register the
          renderer for.

        :param renderer: a callable that should accept a URL argument
          and return a rendered HTML snippet for this resource.

        :param order: optionally, to control the order in which the
          snippets are included in the HTML document. If no order is
          given, the resource will be included after all other resource
          inclusions. The lower the order number, the earlier in the
          rendering the inclusion will appear.
        """

        if order is None:
            order = self._default_order
        else:
            self._default_order = max(self._default_order, order + 1)
        self[extension] = (order, renderer)


inclusion_renderers = InclusionRenderers()

register_inclusion_renderer = inclusion_renderers.register


def render_ico(url):
    return f'<link rel="shortcut icon" type="image/x-icon" href="{url}"/>'


def render_css(url):
    return f'<link rel="stylesheet" type="text/css" href="{url}" />'


def render_js(url):
    return f'<script type="text/javascript" src="{url}"></script>'


def render_print_css(url):
    return (
        f'<link rel="stylesheet" type="text/css" href="{url}" media="print" />'
    )


def render_screen_css(url):
    return (
        '<link rel="stylesheet" type="text/css" media="screen"'
        f' href="{url}" />')


register_inclusion_renderer('.css', render_css, 10)

register_inclusion_renderer('.js', render_js, 20)

register_inclusion_renderer('.ico', render_ico, 30)


class Renderable:
    """A renderable.

    A renderable must have a library attribute and a dependency_nr.
    """

    def render(self, library_url):
        """Render this renderable as something to insert in HTML.

        This returns a snippet.
        """
        raise NotImplementedError()


class Dependable:
    """Dependables have a dependencies and an a resources attributes.
    """
    resources = None
    depends = None
    supports = None

    def add_dependency(self, dependency):
        if dependency in self.depends:
            return
        if dependency in self.list_supporting():
            raise ValueError('Cannot create dependencies loops')
        new_dependencies = set(self.depends)
        new_dependencies.add(dependency)
        self.set_dependencies(new_dependencies)

    def set_dependencies(self, dependencies):
        raise NotImplementedError()

    def list_assets(self):
        raise NotImplementedError()

    def list_supporting(self):
        supports = set()
        for dependable in self.supports:
            supports.add(dependable)
            supports.update(dependable.list_supporting())
        return supports


class Asset(Dependable):
    """An asset can either a resource or a slot.
    """

    def __init__(self, library, depends=None):
        self.library = library
        self.supports = set()
        self.set_dependencies(depends)
        self.library.register(self)

    def set_dependencies(self, depends):
        assert not isinstance(depends, str)
        if depends is not None:
            self.depends = set(depends)
        else:
            self.depends = set()

        self.resources = {self}
        for depend in self.depends:
            depend.supports.add(self)
            self.resources.update(depend.resources)

        # Update resources if needed.
        for dependable in self.list_supporting():
            dependable.resources.update(self.resources)

        # Check for library dependency cycles.
        self.library.check_dependency_cycle(self)

    def list_assets(self):
        return {self}

    def init_dependency_nr(self):
        # on dependency within the library
        dependency_nr = 0
        for depend in self.depends:
            for asset in depend.list_assets():
                dependency_nr = max(asset.dependency_nr + 1, dependency_nr)
        self.dependency_nr = dependency_nr


NOTHING = object()


class Resource(Renderable, Asset):
    """A resource.

    A resource specifies a single resource in a library so that it can
    be included in a web page. This is useful for Javascript and CSS
    resources in particular. Some static resources such as images are
    not included in this way and therefore do not have to be defined
    this way.

    :param library: the :py:class:`Library` this resource is in.

    :param relpath: the relative path (from the root of the library
      path) that indicates the actual resource file.

    :param depends: optionally, a list of resources that this resource
      depends on. Entries in the list are :py:class:`Resource`
      instances.

    :param supersedes: optionally, a list of :py:class:`Resource`
      instances that this resource supersedes as a rollup
      resource. If all these resources are required for render a page,
      the superseding resource will be included instead.

    :param bottom: indicate that this resource is "bottom safe": it
      can be safely included on the bottom of the page (just before
      ``</body>``). This can be used to improve the performance of
      page loads when Javascript resources are in use. Not all
      Javascript-based resources can however be safely included that
      way, so you have to set this explicitly (or use the
      ``force_bottom`` option on :py:class:`NeededResources`).

    :param renderer: optionally, a callable that accepts an URL
      argument and returns a rendered HTML snippet for this
      resource. If no renderer is provided, a renderer is looked up
      based on the resource's filename extension.

    :param dont_bundle: Don't bundle this resource in any bundles
      (if bundling is enabled).

    """

    def __init__(self, library, relpath,
                 depends=None,
                 supersedes=None,
                 bottom=False,
                 renderer=None,
                 debug=None,
                 dont_bundle=False,
                 minified=None,
                 minifier=NOTHING,
                 compiler=NOTHING,
                 source=None,
                 mode_parent=None):
        self.relpath = relpath
        super().__init__(library, depends)
        self.dirname, self.filename = os.path.split(relpath)
        if self.dirname and not self.dirname.endswith('/'):
            self.dirname += '/'
        self.ext = os.path.splitext(self.relpath)[1]

        self.mode_parent = mode_parent
        if compiler is NOTHING:
            compiler = self.library.compilers.get(self.ext)
        self.compiler = fanstatic.registry.CompilerRegistry.instance()[
            compiler]
        self.source = source

        if minifier is NOTHING:
            if mode_parent is None:
                minifier = self.library.minifiers.get(self.ext)
            else:
                minifier = None
        self.minifier = fanstatic.registry.MinifierRegistry.instance()[
            minifier]
        self.minified = minified
        if (self.minified and not isinstance(self.minified, str)
                and self.minifier.available):
            raise ConfigurationError(
                "Since %s specifies minifier %s, passing another "
                "Resource object as its minified version does not make sense"
                % (self.relpath, minifier))
        if not self.minified and self.minifier.available:
            self.minified = self.minifier.source_to_target(self)

        if _resource_file_existence_checking:
            path = self.fullpath()
            minified = (self.mode_parent
                        and self.mode_parent.minifier.available)
            if not (minified
                    or self.compiler.available
                    or os.path.exists(path)):
                raise UnknownResourceError(
                    "Resource file does not exist: %s" % path)
            path = self.compiler.source_path(self)
            if self.compiler.available and not os.path.exists(path):
                raise UnknownResourceError(
                    "Source file {} for {} does not exist".format(
                        path, self.fullpath()))

        self.bottom = bottom
        self.dont_bundle = dont_bundle

        if renderer is None:
            # No custom, ad-hoc renderer for this Resource, so lookup
            # the default renderer by resource filename extension.
            if self.ext not in inclusion_renderers:
                raise UnknownResourceExtensionError(
                    "Unknown resource extension %s for resource: %s" %
                    (self.ext, repr(self)))
            self.order, self.renderer = inclusion_renderers[self.ext]
        else:
            # Use the custom renderer.
            self.renderer = renderer
            # If we do not know about the filename extension inclusion
            # order, we render the resource after all others.
            self.order, _ = inclusion_renderers.get(
                self.ext, (sys.maxsize, None))

        self.modes = {}
        for mode_name, argument in [(DEBUG, debug), (MINIFIED, self.minified)]:
            if argument is None:
                continue
            elif isinstance(argument, str):
                # this if is kludgy, but better than unrolling the loop
                if mode_name == MINIFIED:
                    mode_parent = self.minifier.available and self
                else:
                    mode_parent = None
                mode_resource = Resource(
                    library, argument, bottom=bottom, renderer=renderer,
                    depends=depends, dont_bundle=dont_bundle,
                    mode_parent=mode_parent)
            else:
                # The dependencies of a mode resource should be the same
                # or a subset of the dependencies this mode replaces.
                if len(argument.depends - self.depends) > 0:
                    raise ModeResourceDependencyError
                mode_resource = argument

            self.modes[mode_name] = mode_resource

        assert not isinstance(supersedes, str)
        self.supersedes = supersedes or []

        self.rollups = []
        # create a reference to the superseder in the superseded resource
        for resource in self.supersedes:
            resource.rollups.append(self)

    def fullpath(self, path=None):
        if path is None:
            path = self.relpath
        return os.path.normpath(os.path.join(self.library.path, path))

    def compile(self, force=False):
        # Skip compilation if this library has a version.
        # If a package has been installed in development mode, the Library
        # doesn't have a version. See registry.py.
        if self.library.version is not None:
            return
        if self.mode_parent:
            self.mode_parent.compile(force=force)
        else:
            self.compiler(self, force=force)
            self.minifier(self, force=force)

    def render(self, library_url):
        return self.renderer('{}/{}'.format(library_url, self.relpath))

    def __repr__(self):
        return "<Resource '{}' in library '{}'>".format(
            self.relpath, self.library.name)

    def mode(self, mode):
        """Get Resource in another mode.

        If the mode is ``None`` or if the mode cannot be found, this
        ``Resource`` instance is returned instead.

        :param mode: a string indicating the mode, or ``None``.
        """
        if mode is None:
            return self
        # try getting the alternative
        try:
            return self.modes[mode]
        except KeyError:
            # fall back on the default mode if mode not found
            return self

    def need(self, slots=None):
        """Declare that the application needs this resource.

        If you call ``.need()`` on ``Resource`` sometime during the
        rendering process of your web page, this resource and all its
        dependencies will be inserted as inclusions into the web page.

        :param slots: an optional dictionary mapping from
          :py:class:`Slot` instances to :py:class:`Resource`
          instances. This dictionary describes how to fill in the
          slots that this resource might depend on (directly or
          indirectly). If a slot is required, the dictionary must
          contain an entry for it.
        """
        needed = get_needed()
        needed.need(self, slots)


REQUIRED_DEFAULT_MARKER = object()


class Slot(Asset):
    """A resource slot.

    Sometimes only the application has knowledge on how to fill in a
    dependency for a resource, and this cannot be known at resource
    definition time. In this case you can define a slot, and make your
    resource depend on that. This slot can then be filled in with a
    real resource by the application when you ``.need()`` that
    resource (or when you need something that depends on the slot
    indirectly).

    :param library: the :py:class:`Library` this slot is in.

    :param ext: the extension of the slot, for instance '.js'. This
      determines what kind of resources can be slotted in here.

    :param required: a boolean indicating whether this slot is
      required to be filled in when a resource that depends on a slot
      is needed, or whether it's optional. By default filling in a
      slot is required.

    :param depends: optionally, a list of resources that this slot
      depends on. Resources that are slotted in here need to have
      the same dependencies as that of the slot, or a strict subset.
    """

    def __init__(self, library, extension, depends=None,
                 required=REQUIRED_DEFAULT_MARKER,
                 default=None):
        super().__init__(library, depends)
        # We need to detect if required was set to true explicitly.
        if required is True and default is not None:
            raise ValueError('A slot with a default is not required and can '
                             'not be made required.')
        if required is REQUIRED_DEFAULT_MARKER:
            required = True
        self.default = default
        assert extension.startswith('.')
        self.ext = extension
        self.required = required


class FilledSlot(Renderable):

    def __init__(self, slot, resource):
        self.filledby = resource
        self.library = resource.library
        self.relpath = resource.relpath
        self.dirname, self.filename = resource.dirname, resource.filename
        self.bottom = resource.bottom
        self.rollups = resource.rollups
        self.dont_bundle = resource.dont_bundle
        if slot.ext != resource.ext:
            raise SlotError(
                "slot requires extension %s but filled with resource "
                "with extension %s" %
                (slot.ext, resource.ext))

        self.ext = resource.ext
        self.order = resource.order
        self.renderer = resource.renderer
        self.dependency_nr = slot.dependency_nr

        self.modes = {}
        for key, resource in resource.modes.items():
            self.modes[key] = FilledSlot(slot, resource)

        if not resource.depends.issubset(slot.depends):
            raise SlotError(
                "slot filled in with resource that has dependencies that "
                "are not a strict subset of dependencies of slot")

        # XXX how do slots interact with rollups?

    def render(self, library_url):
        return self.filledby.render(library_url)

    def compile(self, force=False):
        self.filledby.compile(force=force)

    def __repr__(self):
        return "<FilledSlot '{}' in library '{}'>".format(
            self.relpath, self.library.name)

    def mode(self, mode):
        if mode is None:
            return self
        # try getting the alternative
        try:
            return self.modes[mode]
        except KeyError:
            # fall back on the default mode if mode not found
            return self


class Group(Dependable):
    """A resource used to group resources together.

    It doesn't define a resource file itself, but instead depends on
    other resources. When a Group is depended on, all the resources
    grouped together will be included.

   :param depends: a list of resources that this resource depends
     on. Entries in the list can be :py:class:`Resource` instances, or
     :py:class:`Group` instances.
    """

    def __init__(self, depends):
        self.supports = set()
        self.set_dependencies(depends)

    def set_dependencies(self, depends):
        self.depends = set(depends)
        self.resources = set()
        for depend in self.depends:
            depend.supports.add(self)
            self.resources.update(depend.resources)

        for dependable in self.list_supporting():
            dependable.resources.update(self.resources)

    def list_assets(self):
        assets = set()
        for depend in self.depends:
            assets.update(depend.list_assets())
        return assets

    def need(self, slots=None):
        """Need this group resource.

        If you call ``.need()`` on ``Group`` sometime
        during the rendering process of your web page, all dependencies
        of this group resources will be inserted into the web page.

        :param slots: an optional dictionary mapping from
          :py:class:`Slot` instances to :py:class:`Resource`
          instances. This dictionary describes how to fill in the
          slots that this resource might depend on (directly or
          indirectly). If a slot is required, the dictionary must
          contain an entry for it.
        """
        needed = get_needed()
        needed.need(self, slots)


# backwards compatibility alias
GroupResource = Group


class NeededResources:
    """The current selection of needed resources..

    The ``NeededResources`` instance maintains a set of needed
    resources for a particular web page.

    :param versioning: If ``True``, Fanstatic will automatically include
      a version identifier in all URLs pointing to resources.
      Since the version identifier will change when you update a resource,
      the URLs can both be infinitely cached and the resources will always
      be up to date. See also the ``recompute_hashes`` parameter.

    :param versioning_use_md5: If ``True``, Fanstatic will use and md5
      algorithm instead of an algorithm based on the last modification time of
      the Resource files to compute versions. Use md5 if you don't trust your
      filesystem.

    :param recompute_hashes: If ``True`` and versioning is enabled, Fanstatic
      will recalculate hash URLs on the fly whenever you make changes, even
      without restarting the server. This is useful during development,
      but slower, so should be turned off during deployment.
      If set to ``False``, the hash URLs will only be
      calculated once after server startup.

    :param base_url: This URL will be prefixed in front of all resource
      URLs. This can be useful if your web framework wants the resources
      to be published on a sub-URL. By default, there is no ``base_url``,
      and resources are served in the script root. Note that this can
      also be set with the set_base_url method on a ``NeededResources``
      instance.

    :param script_name: The script_name is a fallback for computing
      library URLs. The base_url parameter should be honoured if
      it is provided.

    :param publisher_signature: The name under which resource libraries
      should be served in the URL. By default this is ``fanstatic``, so
      URLs to resources will start with ``/fanstatic/``.

    :param resources: Optionally, a list of resources we want to
      include. Normally you specify resources to include by calling
      ``.need()`` on them, or alternatively by calling ``.need()``
      on an instance of this class.

    """

    _base_url = None
    """The base URL.

    This URL will be prefixed in front of all resource
    URLs. This can be useful if your web framework wants the resources
    to be published on a sub-URL. It is allowed for a web framework
    to change this attribute directly on an already existing
    ``NeededResources`` object.
    """

    def __init__(self,
                 versioning=False,
                 versioning_use_md5=False,
                 recompute_hashes=True,
                 base_url=None,
                 script_name=None,
                 publisher_signature=DEFAULT_SIGNATURE,
                 resources=None,
                 ):
        self._versioning = versioning
        if versioning_use_md5:
            self._version_method = fanstatic.checksum.md5
        else:
            self._version_method = fanstatic.checksum.mtime

        self._recompute_hashes = recompute_hashes
        self._base_url = base_url
        self._script_name = script_name
        self._publisher_signature = publisher_signature
        self._resources = set(resources or [])
        self._slots = {}
        self._url_cache = {}  # prevent multiple computations per request

    def has_resources(self):
        """Returns True if any resources are needed.
        """
        return bool(self._resources)

    def has_base_url(self):
        """Returns True if base_url has been set.
        """
        return self._base_url is not None

    def set_base_url(self, url):
        """Set the base_url. The base_url can only be set (1) if it has not
        been set in the NeededResources configuration and (2) if it has not
        been set before using this method.
        """
        if not self.has_base_url():
            self._base_url = url

    def need(self, resource, slots=None):
        """Add a particular resource to the needed resources.

        This is an alternative to calling ``.need()`` on the resource
        directly.

        :param resource: A :py:class:`Resource` instance.

        :param slots: an optional dictionary mapping from
          :py:class:`Slot` instances to :py:class:`Resource`
          instances. This dictionary describes how to fill in the
          slots that the given resource might depend on (directly or
          indirectly). If a slot is required, the dictionary must
          contain an entry for it.
        """
        slots = slots or {}
        self._resources.add(resource)
        self._slots.update(slots)

    def resources(self):
        """Retrieve the list of resources needed.

        This returns the needed :py:class:`Resource`
        instances.  Resources are guaranteed to come earlier in the
        list than those resources that depend on them.

        Resources are also sorted by extension.
        """
        resources = set()
        for resource in self._resources:
            resources.update(resource.resources)
        return self._fill_slots(resources)

    def _fill_slots(self, resources):
        result = set()
        for resource in resources:
            if not isinstance(resource, Slot):
                result.add(resource)
                continue
            fill_resource = self._slots.get(resource)
            if fill_resource is None:
                if resource.default is not None:
                    fill_resource = resource.default
                elif not resource.required:
                    continue
                else:
                    raise SlotError(
                        "slot %r was required but not filled in" % resource)
            result.add(FilledSlot(resource, fill_resource))
        return result

    def clear(self):
        # Clear out any resources "needed" thusfar.
        # XXX or should we rather revert to the list with resources
        # that potentially was passed as an argument when creating
        # this NeededResources instance?
        self._resources = set()

    def library_url(self, library):
        """Construct URL to library.

        This constructs a URL to a library, obey ``versioning`` and
        ``base_url`` configuration.

        :param library: A :py:class:`Library` instance.
        """
        library_url = self._url_cache.get(library.name)
        if library_url:
            return library_url

        # The script_name is a fallback and base_url should be honoured
        # if it is provided.
        path = [self._base_url or self._script_name or '']
        if self._publisher_signature:
            path.append(self._publisher_signature)
        path.append(library.name)
        if self._versioning:
            path.append(
                library.signature(
                    recompute_hashes=self._recompute_hashes,
                    version_method=self._version_method))
        library_url = self._url_cache[library.name] = '/'.join(path)
        return library_url


class DummyNeededResources:
    """A dummy implementation of the needed resources.

    This class implements the same API as the NeededResources class,
    but refuses to do anything but need() resources. Resources that are
    needed are dropped to the floor.
    """

    def need(self, resource, slots=None):
        pass

    def has_resources(self):
        return False

    def _not_implented_here(self, *args, **kwargs):
        raise NotImplementedError(
            '''
            This functionality is not implemented by objects of the %s class.
            You probably want a NeededResources object.''' %
            self.__class__.__name__)

    clear = _not_implented_here
    library_url = _not_implented_here
    resources = _not_implented_here


thread_local_needed_data = threading.local()


def init_needed(*args, **kw):
    """Initialize a NeededResources object in the thread-local data. Arguments
    are passed verbatim to the NeededResource __init__.
    """
    registry = fanstatic.get_library_registry()
    registry.prepare()
    needed = NeededResources(*args, **kw)
    thread_local_needed_data.__dict__[NEEDED] = needed
    return needed


def del_needed():
    """Delete the NeededResources object from the thread-local data to leave a
    clean environment.

    This function will silently pass whenever there is no NeededResources
    object in the thread-local in the first place.
    """
    try:
        del thread_local_needed_data.__dict__[NEEDED]
    except KeyError:
        pass


def get_needed():
    needed = thread_local_needed_data.__dict__.get(NEEDED)
    if needed is None:
        # When no NeededResources have been set up, we inject a
        # DummyNeededResources object here.
        # We do this in order not to tax other code that may need()
        # a resource here and there but has not set up NeededResources.
        return DummyNeededResources()
    return needed


def clear_needed():
    needed = get_needed()
    needed.clear()


class Bundle(Renderable):

    def __init__(self):
        self._resources = []

    @property
    def dirname(self):
        return self._resources[0].dirname

    @property
    def library(self):
        return self._resources[0].library

    @property
    def renderer(self):
        return self._resources[0].renderer

    @property
    def ext(self):
        return self._resources[0].ext

    @property
    def relpath(self):
        paths = [resource.filename for resource in self._resources]
        return ''.join([self.dirname, BUNDLE_PREFIX, ';'.join(paths)])

    def resources(self):
        """This is used to test resources, not because this is a dependable.
        """
        return self._resources

    def render(self, library_url):
        # URL may become too long:
        # http://www.boutell.com/newfaq/misc/urllength.html
        return self.renderer('{}/{}'.format(library_url, self.relpath))

    def fits(self, resource):
        if resource.dont_bundle:
            return False
        # an empty resource fits anything
        if not self._resources:
            return True
        # a resource fits if it's like the resources already inside
        bundle_resource = self._resources[0]
        return (resource.library is bundle_resource.library and
                resource.renderer is bundle_resource.renderer and
                resource.dirname == bundle_resource.dirname)

    def append(self, resource):
        self._resources.append(resource)

    def add_to_list(self, result):
        """Add the bundle to list, taking single-resource bundles into account.
        """
        amount = len(self._resources)
        if amount == 0:
            # empty bundle; don't add it to list
            return
        elif amount == 1:
            # if it only contains a single entry, add it by itself
            result.append(self._resources[0])
        else:
            # add the bundle itself
            result.append(self)
