import sys

import setuptools.command.sdist

from fanstatic.compiler import _compile_resources


class sdist_compile(setuptools.command.sdist.sdist):

    def run(self):
        self._activate_distribution()
        for package in self.distribution.packages:
            _compile_resources(package)
        # this is kludgy. egg_info does two things, writing egg-info *and*
        # finding all files. But since we generate more files, we need to
        # trigger the finding step again to have them picked up.
        self.get_finalized_command('egg_info').find_sources()
        setuptools.command.sdist.sdist.run(self)  # old-style super()

    def _activate_distribution(self):
        """Make our distribution available in this Python interpreter,
        so that we can access its entry points and import it.
        """
        # We need egg-info e.g. to load entrypoints.
        # Since our superclass runs egg_info as its first action anyway (and
        # commands are run only once), there's no harm in doing it even
        # earlier here.
        self.run_command('egg_info')
        for directory in self.distribution.package_dir.values():
            sys.path.insert(0, directory)
