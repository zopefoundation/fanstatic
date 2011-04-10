import os
import hashlib

VCS_NAMES = ['.svn', '.git', '.bzr', '.hg']
IGNORED_EXTENSIONS = ['.swp', '.tmp', '.pyc', '.pyo']


def list_directory(path):
    # Skip over any VCS directories.
    for root, dirs, files in os.walk(path):
        for dir in VCS_NAMES:
            try:
                dirs.remove(dir)
            except ValueError:
                pass
        # We are also interested in the directories.
        yield os.path.join(root)
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in IGNORED_EXTENSIONS:
                continue
            yield os.path.join(root, file)


def checksum(path):
    chcksm = hashlib.md5()
    for path in list_directory(path):
        chcksm.update(path)
        chcksm.update(str(os.stat(path).st_mtime))
    return chcksm.hexdigest()
