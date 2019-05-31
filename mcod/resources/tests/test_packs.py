import pytest
import os

from mcod.lib.utils import extract_resource, cleanup_extracted, analyze_resource_file, UnsupportedArchiveError
from .conftest import prepare_file


@pytest.mark.django_db
class TestPackedResources:
    def test_unpacking_and_cleaning(self):
        for extension in ('zip', 'rar', '7z', 'tar.gz', 'tar.bz2'):
            archive = f'empty_file.{extension}'
            extracted = extract_resource(prepare_file(archive))
            assert extracted
            assert len(extracted) == 1
            assert os.path.isfile(extracted[0]) is True

            cleanup_extracted(extracted)
            assert os.path.exists(extracted[0]) is False

        extracted = extract_resource(prepare_file('multi_file.rar'))
        assert extracted
        assert len(extracted) == 2
        for path in extracted:
            assert os.path.isfile(path) is True
        cleanup_extracted(extracted)
        for path in extracted:
            assert os.path.exists(path) is False

    def test_single_file_pack(self, single_file_pack):
        extension, file_info, encoding, extracted = analyze_resource_file(single_file_pack)
        print(extension, file_info, encoding)
        assert os.path.isfile(extracted) is True
        assert extension == 'csv'

    def test_multi_file_pack(self, multi_file_pack):
        with pytest.raises(UnsupportedArchiveError) as e:
            assert analyze_resource_file(multi_file_pack)
        assert str(e.value) == 'archives-are-not-supported'

    def test_spreedsheet_with_assertion(self, spreedsheet_xlsx_pack):
        extension, file_info, encoding, extracted = analyze_resource_file(spreedsheet_xlsx_pack)
        assert extracted is spreedsheet_xlsx_pack
        assert extension == 'xlsx'
        assert encoding == 'Windows-1250'

    def test_document_with_assertion(self, document_docx_pack):
        extension, file_info, encoding, extracted = analyze_resource_file(document_docx_pack)
        assert extracted is document_docx_pack
        assert extension == 'docx'
        assert encoding == 'Windows-1250'

    def test_shapefile(self, shapefile):
        extension, file_info, encoding, extracted = analyze_resource_file(shapefile)
        assert extracted is shapefile
        assert extension == 'shp'
        assert encoding == 'utf-8'
