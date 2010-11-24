import os
import zlib

def list_directory(path):
    # ignore any VCS directories
    ignored_dirs = ['.svn', '.git', '.bzr']
    for root, dirs, files in os.walk(path):
        for dir in ignored_dirs:
            try:
                dirs.remove(dir)
            except ValueError:
                pass
        for file in files:
            yield os.path.join(root, file)

def checksum(path):
    # ignored extensions
    ignored_extensions = ['.swp', '.tmp', '.pyc']

    data = ''
    for path in list_directory(path):
        for ext in ignored_extensions:
            if path.endswith(ext):
               continue
        f = open(path, 'rb')
        data += path + f.read()
        f.close()
    return zlib.adler32(data) & 0xffffffff

