import zest.releaser.utils
import pkg_resources


# http://zestreleaser.readthedocs.org/en/latest/entrypoints.html
def compile_resources(context):
    project_name = context['name']
    zest.releaser.utils.logger.info(
        'Compiling resources for {}'.format(project_name))

    dist = pkg_resources.get_distribution(project_name)

    # A dist may contain multiple libraries.
    for entry_point in pkg_resources.get_entry_map(
            dist, group='fanstatic.libraries').values():
        library = entry_point.load()

        for resource in library.known_resources.values():
            zest.releaser.utils.logger.info(
                'Compiling {}'.format(resource))
            resource.compile(force=True)
