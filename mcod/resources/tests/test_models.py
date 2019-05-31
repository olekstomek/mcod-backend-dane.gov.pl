import json
from datetime import date

import pytest
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from mcod.resources.models import Resource, TaskResult


@pytest.mark.django_db
class TestResourceModel(object):
    def test_resource_fields(self, valid_resource):
        r_dict = valid_resource.__dict__
        fields = [
            "uuid",
            "file",
            "format",
            "description",
            "position",
            "old_customfields",
            "title",
            "id",
            "dataset_id",
            "link",
            "is_removed",
            "created",
            "modified",
            "status",
            "modified_by_id",
            "created_by_id",
        ]

        for f in fields:
            assert f in r_dict

    def test_resource_create(self, valid_dataset):
        r = Resource()
        # r.name = "test"
        r.title = "test"
        r.description = "Opis zasobu"
        r.format = "csv"
        r.resource_type = "zestawienie"
        r.old_resource_type = "zestawienie"
        r.dataset = valid_dataset
        r.link = "http://test.to.resource.pl/1.xls"
        r.data_date = "2018-10-02"
        assert r.full_clean() is None
        assert r.id is None
        r.save()
        assert r.id is not None

    def test_resource_safe_delete(self, valid_resource):
        assert valid_resource.status == 'published'
        valid_resource.delete()
        assert valid_resource.is_removed is True
        assert Resource.deleted.get(id=valid_resource.id)
        assert Resource.raw.get(id=valid_resource.id)
        with pytest.raises(ObjectDoesNotExist):
            Resource.objects.get(id=valid_resource.id)

    def test_resource_unsafe_delete(self, valid_resource):
        assert valid_resource.status == 'published'
        valid_resource.delete(soft=False)
        with pytest.raises(ObjectDoesNotExist):
            Resource.raw.get(id=valid_resource.id)
        with pytest.raises(ObjectDoesNotExist):
            Resource.deleted.get(id=valid_resource.id)

    def test_file_url_and_path(self, valid_resource, mocker):
        mocker.patch('mcod.resources.tasks.download_file', return_value=('file', {}))
        assert not valid_resource.file
        valid_resource.file = SimpleUploadedFile("somefile.jpg", b"""1px""")
        valid_resource.save()
        assert valid_resource.file
        date_folder = date.today().isoformat().replace('-', '')
        file_name = valid_resource.file.name
        assert valid_resource.file.url == f"/media/resources/{file_name}"
        assert valid_resource.file.path == f"{settings.RESOURCES_MEDIA_ROOT}/{file_name}"
        assert date_folder in valid_resource.file.url
        assert date_folder in valid_resource.file.path

        assert len(TaskResult.objects.all()) == 3
        valid_resource.revalidate()
        assert len(TaskResult.objects.all()) == 6


@pytest.mark.django_db
class TestTaskResultModel:
    def test_result_parser(self):
        exc_message = [
            {
                "code": 'sth-gone-wrong',
                "delta": "triangle",
                "other_message": "it's a trap",
                "'code'": "another trap",
                "test": "test",
                "message": "Coś się nie udało",
            },
            {
                "code": 'second-error',
                "message": "second error message",
                "test": "boom"
            }
        ]
        result = {
            'exc': 'some_value',
            'message': "Try to break this",
            'alpha': "romeo",
            'bravo': "fiat",
            'exc_message': str(exc_message),
            "charlie": "chaplin",
        }
        for key in ['message', 'code', 'test']:
            count = 0
            for msg in TaskResult.values_from_result(result, key):
                assert msg == exc_message[count].get(key)
                count += 1
            assert count == len(exc_message)

        with pytest.raises(KeyError):
            for msg in TaskResult.values_from_result(result, 'other_message'):
                pass

    def test_messages_on_success(self, valid_resource_with_file):
        resource = valid_resource_with_file

        for tasks in (resource.file_tasks, resource.link_tasks, resource.data_tasks):
            assert tasks.count() == 1
            task = tasks.first()
            assert task.status == 'SUCCESS'
            assert isinstance(task.message, list)
            assert len(task.message) == 1
            assert task.message[0] == ""

            assert isinstance(task.recommendation, list)
            assert len(task.recommendation) == 1
            assert task.recommendation[0] == ''

    def test_data_messages_on_failure(self, table_resource_with_invalid_schema):
        resource = table_resource_with_invalid_schema
        task = resource.data_tasks.first()
        assert task.status == 'FAILURE'
        assert isinstance(task.message, list)
        assert isinstance(task.recommendation, list)
        assert len(task.message) == len(task.recommendation)
        assert len(task.message) > 0

        for msg in task.message:
            assert isinstance(msg, str)
            assert len(msg) > 5

        for msg in task.recommendation:
            assert isinstance(msg, str)
            assert len(msg) > 5

        assert task.message[0].startswith("Błąd schematu tabeli:")
        assert task.recommendation[0].startswith("Zaktualizuj deskryptor schematu")

        task.result = json.dumps({
            'exc_type': "SomeUnknownException",
            'exc_message': "Some unknown exception was thrown and You should not know what to do with it."
        })
        task.save()

        assert task.message[0] == "Nierozpoznany błąd walidacji"
        assert task.recommendation[0] == "Skontaktuj się z administratorem systemu."

    def test_error_code_finding(self):
        result = {
            'exc_type': "TestError",
            'exc_message': ""
        }
        assert TaskResult._find_error_code(result) == 'TestError'

        result['exc_type'] = 'OperationalError'
        result['exc_message'] = "could not connect to server: Connection refused, cośtam cośtam"
        assert TaskResult._find_error_code(result) == 'connection-error'
        result['exc_message'] = "Lorem ipsum remaining connection slots are reserved cośtam dalej"
        assert TaskResult._find_error_code(result) == 'connection-error'

        result['exc_type'] = "Exception"
        result['exc_message'] = "unknown-file-format"

        assert TaskResult._find_error_code(result) == 'unknown-file-format'

        result = {
            "exc_type": "InvalidResponseCode",
            "exc_message": "Invalid response code: 404"
        }
        assert TaskResult._find_error_code(result) == '404-not-found'

        result = {
            "exc_type": "ConnectionError",
            "exc_message": "HTTPSConnectionPool(host='knmiof.mac.gov.pl', port=443): Max retries exceeded with url: "
                           "/kn/aktualnosci/6159,Nowy-wykaz-urzedowych-nazw-miejscowosci.html (Caused by "
                           "NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x7f1418374dd8>: "
                           "Failed to establish a new connection: [Errno -2] Name or service not known',))",
        }
        assert TaskResult._find_error_code(result) == 'failed-new-connection'
