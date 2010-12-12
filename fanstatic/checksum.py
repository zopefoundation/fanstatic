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
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in IGNORED_EXTENSIONS:
                continue
            yield os.path.join(root, file)

def checksum(path):
    # Ignored extensions.
    chcksm = hashlib.md5()
    for path in list_directory(path):
        # Use the full path name too for the checksum too to track file renames.
        chcksm.update(path)
        try:
            f = open(path, 'rb')
            while True:
                # 256kb chunks.
                # XXX how to optimize chunk size?
                chunk = f.read(0x40000)
                if not chunk:
                    break
                chcksm.update(chunk)
        finally:
            f.close()
    return chcksm.hexdigest()

