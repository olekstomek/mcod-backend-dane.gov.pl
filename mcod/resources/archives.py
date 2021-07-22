import libarchive
import os
import tempfile


ARCHIVE_CONTENT_TYPES = {
    'gzip', 'x-gzip', 'vnd.rar', 'rar', 'x-rar', 'x-rar-compressed', 'x-7z-compressed',
    'x-bzip', 'bzip2', 'x-bzip2', 'x-tar', 'x-zip-compressed', 'zip'
}

ARCHIVE_EXTENSIONS = {'gz', 'rar', '7zip', 'bz', 'bz2', 'tar', 'zip'}


class UnsupportedArchiveError(Exception):
    pass


def is_archive_file(content_type):
    return content_type in ARCHIVE_CONTENT_TYPES


def has_archive_extension(path):
    ext = path.rsplit('.', 1)[-1]
    return ext in ARCHIVE_EXTENSIONS


class ArchiveReader(object):
    _tmp_dir = None

    def __init__(self, source, destiny_path=None):
        root_dir = os.path.realpath(destiny_path or self.tmp_dir)

        files = []

        with libarchive.file_reader(source) as arch:
            for entry in arch:
                entry_path = self._get_entry_path(entry)
                if entry.isdir:
                    os.makedirs(os.path.join(root_dir, entry_path))
                else:
                    path, extr_file = os.path.split(entry_path)
                    if path and not os.path.isdir(os.path.join(root_dir, path)):
                        os.makedirs(os.path.join(root_dir, path), exist_ok=True)
                    resource_path = os.path.join(root_dir, path, extr_file)

                    with open(resource_path, 'wb') as f:
                        for block in entry.get_blocks():
                            f.write(block)
                    files.append(resource_path)

        self.files = tuple(files)

    @staticmethod
    def _get_entry_path(entry):
        if isinstance(entry.path, str):
            return entry.path
        try:
            entry_path = entry.path.decode()
        except UnicodeDecodeError:
            entry_path = entry.path.decode('iso8859_2')
        return entry_path

    @property
    def tmp_dir(self):
        if not self._tmp_dir:
            self._tmp_dir = tempfile.mkdtemp()
        return self._tmp_dir

    def cleanup(self):
        dirs = set()
        for f in self.files:
            dirs.add(os.path.split(f)[0])
            os.remove(f)

        dirs = sorted(dirs, reverse=True)
        for d in dirs:
            try:
                os.rmdir(d)
            except OSError:
                pass

        if self._tmp_dir:
            try:
                os.rmdir(self._tmp_dir)
            except OSError:
                pass

    def __len__(self):
        return len(self.files)

    def __getitem__(self, item):
        return self.files[item]

    def __enter__(self):
        return self

    def __iter__(self):
        return iter(self.files)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
