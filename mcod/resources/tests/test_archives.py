import os

from mcod.resources.archives import ArchiveReader
from mcod.resources.tests.conftest import prepare_file


class TestArchiveReader:
    def test_reader(self):
        for extension in ('zip', 'rar', '7z', 'tar.gz', 'tar.bz2'):
            archive = f'empty_file.{extension}'
            with ArchiveReader(prepare_file(archive)) as extracted:
                assert os.path.exists(extracted.tmp_dir) is True
                assert extracted
                assert len(extracted) == 1
                assert os.path.isfile(extracted[0]) is True
            assert os.path.exists(extracted.tmp_dir) is False

            with ArchiveReader(prepare_file('multi_file.rar')) as extracted:
                assert os.path.exists(extracted.tmp_dir) is True
                assert extracted
                assert len(extracted) == 2
                for path in extracted:
                    assert os.path.isfile(path) is True
            assert os.path.exists(extracted.tmp_dir) is False
