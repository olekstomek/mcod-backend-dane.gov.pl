import os
import typing
from uuid import uuid4

import pytest

from mcod.core.storages import ApplicationImagesStorage, OrganizationImagesStorage, ResourcesStorage

if typing.TYPE_CHECKING:
    from pathlib import Path


class TestMediaStorages:
    @staticmethod
    def _test_storage(tmp_path: "Path", storage_cls):
        storage_location = tmp_path / str(uuid4())
        storage = storage_cls(
            location=str(storage_location),
            base_url="/media/%s/" % storage_location.name,
        )
        tmp_name = str(uuid4())
        tmp_file_path = tmp_path / str(uuid4())
        tmp_content = str(uuid4())

        tmp_file_path.write_text(tmp_content)

        with tmp_file_path.open("r") as tmp_file:
            filename1 = storage.save("%s.txt" % tmp_name, tmp_file)
            filename2 = storage.save("%s.txt" % tmp_name, tmp_file)

        base_location = storage.base_location
        base_url = storage.base_url

        file1 = os.path.join(base_location, filename1)
        file2 = os.path.join(base_location, filename2)

        url1 = "%s%s" % (base_url, filename1)
        url2 = "%s%s" % (base_url, filename2)

        assert os.path.exists(base_location) is True
        assert os.path.exists(file1) is True
        assert os.path.exists(file2) is True
        with open(file1, "rt") as f:
            assert f.readline() == tmp_content

        assert filename1 == storage.name_from_url(url1)
        assert filename2 == storage.name_from_url(url2)

        os.remove(file1)
        assert storage.name_from_url(url1) is None
        assert filename2 == storage.name_from_url(url2)

    @pytest.mark.run(order=0)
    def test_resources_storage(self, tmp_path):
        self._test_storage(tmp_path, ResourcesStorage)

    @pytest.mark.run(order=0)
    def test_application_storage(self, tmp_path):
        self._test_storage(tmp_path, ApplicationImagesStorage)

    @pytest.mark.run(order=0)
    def test_organization_storage(self, tmp_path):
        self._test_storage(tmp_path, OrganizationImagesStorage)
