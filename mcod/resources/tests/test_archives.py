import pytest
import os

from mcod.resources.archives import UnsupportedArchiveError, ArchiveReader
from mcod.resources.file_validation import analyze_resource_file
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


class TestPackedResources:
    def test_single_file_pack(self, single_file_pack):
        extension, file_info, encoding, extracted, file_mimetype = analyze_resource_file(single_file_pack)
        assert extension == 'csv'

    def test_multi_file_pack(self, multi_file_pack):
        with pytest.raises(UnsupportedArchiveError) as e:
            assert analyze_resource_file(multi_file_pack)
        assert str(e.value) == 'archives-are-not-supported'

    def test_spreedsheet_with_assertion(self, spreedsheet_xlsx_pack):
        extension, file_info, encoding, extracted, file_mimetype = analyze_resource_file(spreedsheet_xlsx_pack)
        assert extracted is spreedsheet_xlsx_pack
        assert extension == 'xlsx'
        assert encoding == 'Windows-1250'

    def test_document_with_assertion(self, document_docx_pack):
        extension, file_info, encoding, extracted, file_mimetype = analyze_resource_file(document_docx_pack)
        assert extracted is document_docx_pack
        assert extension == 'docx'
        assert encoding == 'Windows-1250'

    # def test_shapefile(self, shapefile_arch):
    #     extension, file_info, encoding, extracted = analyze_resource_file(shapefile_arch)
    #     assert extracted is shapefile_arch
    #     assert extension == 'shp'
    #     assert encoding == 'utf-8'
