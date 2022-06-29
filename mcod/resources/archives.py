import os
import tempfile
import zipfile

import libarchive
import magic
import py7zr
import rarfile
from mimeparse import parse_mime_type

from mcod import settings


class UnsupportedArchiveError(Exception):
    pass


def is_archive_file(content_type):
    return content_type in settings.ARCHIVE_CONTENT_TYPES


def is_password_protected_7z(source):
    if not py7zr.is_7zfile(source):
        return False
    try:
        with py7zr.SevenZipFile(source) as file:
            return file.needs_password()
    except py7zr.PasswordRequired:
        return True


def is_password_protected_zip(source):
    try:
        with zipfile.ZipFile(source) as zip_file:
            for zinfo in zip_file.filelist:
                is_encrypted = zinfo.flag_bits & 0x1
                if is_encrypted:
                    return True
    except zipfile.BadZipFile:
        pass
    return False


def is_password_protected_rar(source):
    if not rarfile.is_rarfile(source):
        return False
    try:
        with rarfile.RarFile(source) as file:
            return file.needs_password()
    except rarfile.PasswordRequired:
        return True


def get_memory_file_info(file):
    _magic = magic.Magic(mime=True, mime_encoding=True)
    result = _magic.from_buffer(file.read(1024))
    file.seek(0)
    return parse_mime_type(result)


def is_password_protected_archive_file(file):
    family, content_type, options = get_memory_file_info(file)
    content_type_2_func = {
        **{
            ct: is_password_protected_rar
            for ct in settings.ARCHIVE_RAR_CONTENT_TYPES
        },
        **{
            ct: is_password_protected_7z
            for ct in settings.ARCHIVE_7Z_CONTENT_TYPES
        },
        **{
            ct: is_password_protected_zip
            for ct in settings.ARCHIVE_ZIP_CONTENT_TYPES
        },
    }
    if content_type not in content_type_2_func:
        return False

    return content_type_2_func[content_type](getattr(file, 'file', file))


def has_archive_extension(path):
    ext = path.rsplit('.', 1)[-1]
    return ext in settings.ARCHIVE_EXTENSIONS


class ArchiveReader:
    _tmp_dir = None

    def __init__(self, source, destiny_path=None):
        root_dir = os.path.realpath(destiny_path or self.tmp_dir)

        files = []
        if rarfile.is_rarfile(source):
            with rarfile.RarFile(source) as rf:
                rf.extractall(path=root_dir)
            for root, dirs, files_ in os.walk(root_dir):
                for filename in files_:
                    files.append(os.path.abspath(os.path.join(root, filename)))

        else:
            with libarchive.file_reader(source) as arch:
                for entry in arch:
                    entry_path = self._get_entry_path(entry)
                    if entry.isdir:
                        os.makedirs(os.path.join(root_dir, entry_path), exist_ok=True)
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
