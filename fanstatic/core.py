import os
import sys
import pkg_resources
import threading

from fanstatic.checksum import checksum

EXTENSIONS = ['.css', '.kss', '.js']

NEEDED = 'fanstatic.needed'

class UnknownResourceExtension(Exception):
    """Unknown resource extension"""

class Library(object):

    _signature = None

    def __init__(self, name, rootpath):
        self.name = name
        self.rootpath = rootpath
        self.path = os.path.join(caller_dir(), rootpath)

    def signature(self, devmode=False):
        if devmode:
            # Always re-compute.
            sig = checksum(self.path)
        elif self._signature is None:
            # Only compute if not conputed before.
            sig = self._signature = checksum(self.path)
        else:
            # Use cached value.
            sig = self._signature
        return ':hash:%s' % sig

# Total hack to be able to get the dir the resources will be in.
def caller_dir():
    return os.path.dirname(sys._getframe(2).f_globals['__file__'])

def _libraries(libs={}):
    if not libs:
        for entry_point in pkg_resources.iter_entry_points(
            'fanstatic.libraries'):
            libs[entry_point.name] = entry_point.load()
    return libs
    
def libraries():
    return _libraries().itervalues()

def library_by_name(name):
    return _libraries()[name]

class InclusionBase(object):
    pass

class ResourceInclusion(InclusionBase):
    """Resource inclusion

    A resource inclusion specifies how to include a single resource in
    a library.
    """

    def __init__(self, library, relpath, depends=None,
                 supersedes=None, eager_superseder=False,
                 bottom=False, **kw):
        """Create a resource inclusion

        library  - the library this resource is in
        relpath  - the relative path from the root of the library indicating
                   the actual resource
        depends  - optionally, a list of resources that this resource depends
                   on. Entries in the list can be
                   ResourceInclusions or strings indicating the path.
                   In case of a string, a ResourceInclusion assumed based
                   on the same library as this inclusion.
        supersedes - optionally, a list of resources that this resource
                   supersedes as a rollup resource. If all these
                   resources are required, the superseding resource
                   instead will show up.
        eager_superseder - even if only part of the requirements are
                           met, supersede anyway
        bottom - optionally, indicate that this resource can be
                 safely included on the bottom of the page (just
                 before ``</body>``). This can be used to
                 improve the performance of page loads when javascript
                 resources are in use. Not all javascript-based resources
                 can however be safely included that way.
        keyword arguments - different paths that represent the same
                  resource in different modes (debug, minified, etc),
                  or alternatively a fully specified ResourceInclusion.
        """
        self.library = library
        self.relpath = relpath
        self.bottom = bottom

        assert not isinstance(depends, basestring)
        depends = depends or []
        self.depends = normalize_inclusions(library, depends)

        self.rollups = []

        normalized_modes = {}
        for mode_name, inclusion in kw.items():
            normalized_modes[mode_name] = normalize_inclusion(
                library, inclusion)
        self.modes = normalized_modes

        assert not isinstance(supersedes, basestring)
        self.supersedes = supersedes or []
        self.eager_superseder = eager_superseder

        # create a reference to the superseder in the superseded inclusion
        for inclusion in self.supersedes:
            inclusion.rollups.append(self)
        # also create a reference to the superseding mode in the superseded
        # mode
        # XXX what if mode is full-fledged resource inclusion which lists
        # supersedes itself?
        for mode_name, mode in self.modes.items():
            for inclusion in self.supersedes:
                superseded_mode = inclusion.mode(mode_name)
                # if there is no such mode, let's skip it
                if superseded_mode is inclusion:
                    continue
                mode.supersedes.append(superseded_mode)
                superseded_mode.rollups.append(mode)

    def __repr__(self):
        return "<ResourceInclusion '%s' in library '%s'>" % (
            self.relpath, self.library.name)

    def ext(self):
        name, ext = os.path.splitext(self.relpath)
        return ext

    def mode(self, mode):
        if mode is None:
            return self
        # try getting the alternative
        try:
            return self.modes[mode]
        except KeyError:
            # fall back on the default mode if mode not found
            return self

    def key(self):
        return self.library.name, self.relpath

    def need(self):
        needed = get_current_needed_inclusions()
        needed.need(self)

    def inclusions(self):
        """Get all inclusions needed by this inclusion, including itself.
        """
        result = []
        for depend in self.depends:
            result.extend(depend.inclusions())
        result.append(self)
        return result

class GroupInclusion(InclusionBase):
    """An inclusion used to group resources together.

    It doesn't define a resource itself.
    """
    def __init__(self, depends):
        self.depends = depends

    def need(self):
        needed = get_current_needed_inclusions()
        needed.need(self)

    def inclusions(self):
        """Get all inclusions needed by this inclusion.
        """
        result = []
        for depend in self.depends:
            result.extend(depend.inclusions())
        return result

def normalize_inclusions(library, inclusions):
    return [normalize_inclusion(library, inclusion)
            for inclusion in inclusions]

def normalize_inclusion(library, inclusion):
    if isinstance(inclusion, InclusionBase):
        return inclusion
    assert isinstance(inclusion, basestring)
    return ResourceInclusion(library, inclusion)

class NeededInclusions(object):
    def __init__(self,
                 base_url='',
                 inclusions=None,
                 mode=None,
                 rollup=False,
                 bottom=False,
                 force_bottom=False,
                 devmode=False,
                 hashing=False,
                 publisher_signature='fanstatic'
                 ):
        self.base_url = base_url
        self._inclusions = inclusions or []
        self._mode = mode
        self._rollup = rollup
        self._bottom = bottom
        self._force_bottom = force_bottom
        self.devmode = devmode
        self.hashing = hashing
        self.publisher_signature = publisher_signature

    def __len__(self):
        return len(self._inclusions)

    def need(self, inclusion):
        self._inclusions.append(inclusion)

    def _sorted_inclusions(self):
        return reversed(sorted(self._inclusions, key=lambda i: i.depth()))

    def inclusions(self):
        inclusions = []
        for inclusion in self._inclusions:
            inclusions.extend(inclusion.inclusions())

        inclusions = apply_mode(inclusions, self._mode)
        if self._rollup:
            inclusions = consolidate(inclusions)
        # sort only by extension, not dependency, as we can rely on
        # python's stable sort to keep inclusion order intact
        inclusions = sort_inclusions_by_extension(inclusions)
        inclusions = remove_duplicates(inclusions)

        return inclusions

    def library_url(self, library):
        segments = [self.base_url, self.publisher_signature]
        if self.hashing:
            segments.append(library.signature(devmode=self.devmode))
        segments.append(library.name)
        return '/'.join(segments)

    def render(self):
        """Render a set of inclusions.
        """
        return self.render_inclusions(self.inclusions())

    def render_inclusions(self, inclusions):
        result = []
        url_cache = {} # prevent multiple computations for a library in one request
        for inclusion in inclusions:
            library = inclusion.library
            library_url = url_cache.get(library.name)
            if library_url is None:
                library_url = url_cache[library.name] = self.library_url(
                    library)
            result.append(
                render_inclusion(
                    inclusion, '%s/%s' %(library_url, inclusion.relpath)))
        return '\n'.join(result)

    def render_into_html(self, html):
        to_insert = self.render()
        return html.replace('<head>', '<head>\n    %s\n' % to_insert, 1)

    def render_topbottom(self):
        inclusions = self.inclusions()

        # seperate inclusions in top and bottom inclusions if this is needed
        if self._bottom:
            top_inclusions = []
            bottom_inclusions = []
            if not self._force_bottom:
                for inclusion in inclusions:
                    if inclusion.bottom:
                        bottom_inclusions.append(inclusion)
                    else:
                        top_inclusions.append(inclusion)
            else:
                for inclusion in inclusions:
                    if inclusion.ext() == '.js':
                        bottom_inclusions.append(inclusion)
                    else:
                        top_inclusions.append(inclusion)
        else:
            top_inclusions = inclusions
            bottom_inclusions = []

        return (self.render_inclusions(top_inclusions),
                self.render_inclusions(bottom_inclusions))

    def render_topbottom_into_html(self, html):
        top, bottom = self.render_topbottom()
        if top:
            html = html.replace('<head>', '<head>\n    %s\n' % top, 1)
        if bottom:
            html = html.replace('</body>', '%s</body>' % bottom, 1)
        return html

class NoNeededInclusions(Exception):
    pass

thread_local_needed_data = threading.local()

def init_current_needed_inclusions(*args, **kw):
    needed = NeededInclusions(*args, **kw)
    thread_local_needed_data.__dict__[NEEDED] = needed
    return needed

def get_current_needed_inclusions():
    needed = thread_local_needed_data.__dict__.get(NEEDED)
    if needed is None:
        raise NoNeededInclusions('No NeededInclusions object initialized.')
    return needed

def apply_mode(inclusions, mode):
    return [inclusion.mode(mode) for inclusion in inclusions]

def remove_duplicates(inclusions):
    """Given a set of inclusions, consolidate them so each only occurs once.
    """
    seen = set()
    result = []
    for inclusion in inclusions:
        if inclusion.key() in seen:
            continue
        seen.add(inclusion.key())
        result.append(inclusion)
    return result

def consolidate(inclusions):
    # keep track of rollups: rollup key -> set of inclusion keys
    potential_rollups = {}
    for inclusion in inclusions:
        for rollup in inclusion.rollups:
            s = potential_rollups.setdefault(rollup.key(), set())
            s.add(inclusion.key())

    # now go through inclusions, replacing them with rollups if
    # conditions match
    result = []
    for inclusion in inclusions:
        eager_superseders = []
        exact_superseders = []
        for rollup in inclusion.rollups:
            s = potential_rollups[rollup.key()]
            if rollup.eager_superseder:
                eager_superseders.append(rollup)
            if len(s) == len(rollup.supersedes):
                exact_superseders.append(rollup)
        if eager_superseders:
            # use the eager superseder that rolls up the most
            eager_superseders = sorted(eager_superseders,
                                       key=lambda i: len(i.supersedes))
            result.append(eager_superseders[-1])
        elif exact_superseders:
            # use the exact superseder that rolls up the most
            exact_superseders = sorted(exact_superseders,
                                       key=lambda i: len(i.supersedes))
            result.append(exact_superseders[-1])
        else:
            # nothing to supersede resource so use it directly
            result.append(inclusion)
    return result

def sort_inclusions_by_extension(inclusions):

    def key(inclusion):
        return EXTENSIONS.index(inclusion.ext())

    return sorted(inclusions, key=key)

def sort_inclusions_topological(inclusions):
    """Sort inclusions by dependency and supersedes.
    """
    dead = {}
    result = []
    for inclusion in inclusions:
        dead[inclusion.key()] = False

    for inclusion in inclusions:
        _visit(inclusion, result, dead)
    return result

def _visit(inclusion, result, dead):
    if dead[inclusion.key()]:
        return
    dead[inclusion.key()] = True
    for depend in inclusion.depends:
        _visit(depend, result, dead)
    for depend in inclusion.supersedes:
        _visit(depend ,result, dead)
    result.append(inclusion)

def render_css(url):
    return ('<link rel="stylesheet" type="text/css" href="%s" />' %
            url)

def render_kss(url):
    raise NotImplementedError

def render_js(url):
    return ('<script type="text/javascript" src="%s"></script>' %
            url)

inclusion_renderers = {
    '.css': render_css,
    '.kss': render_kss,
    '.js': render_js,
    }

def render_inclusion(inclusion, url):
    renderer = inclusion_renderers.get(inclusion.ext(), None)
    if renderer is None:
        raise UnknownResourceExtension(
            "Unknown resource extension %s for resource inclusion: %s" %
            (inclusion.ext(), repr(inclusion)))
    return renderer(url)

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
