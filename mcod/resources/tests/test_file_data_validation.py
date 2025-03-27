import os

import factory
from django.conf import settings

from mcod.resources.factories import ResourceFactory


def test_smoke_resource_data_validation():
    res = ResourceFactory.create(
        type="file",
        format="xlsx",
        main_file__file=factory.django.FileField(
            from_path=os.path.join(settings.TEST_SAMPLES_PATH, "plik_testowy.xlsx"),
            filename="plik_testowy.xlsx",
        ),
    )
    res.data.validate()
