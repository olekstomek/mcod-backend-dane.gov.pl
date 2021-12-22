import pytest
import requests_mock

from mcod.resources.link_validation import (
    check_link_status, InvalidUrl, InvalidResponseCode, InvalidSchema,
    InvalidContentType, UnsupportedContentType, download_file, MissingContentType,
    content_type_from_file_format, filename_from_url,
    _get_resource_type
)


class TestCheckLinkStatus:

    url = 'http://mocker-test.com'

    def test_throw_invalid_url(self):
        try:
            check_link_status('www.brokenlink', 'api')
            raise pytest.fail('No exception occurred. Expected: InvalidUrl')
        except InvalidUrl as err:
            assert err.args[0] == 'Invalid url address: www.brokenlink'

    @requests_mock.Mocker(kw='mock_request')
    def test_throw_invalid_response_code(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'application/json'}
        mock_request.head(self.url, headers=headers, status_code=504)
        try:
            check_link_status(self.url, 'api')
            raise pytest.fail('No exception occurred. Expected: InvalidResponseCode')
        except InvalidResponseCode as err:
            assert err.args[0] == 'Invalid response code: 504'

    @requests_mock.Mocker(kw='mock_request')
    def test_invalid_content_type(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'application/text/json'}
        mock_request.head(self.url, headers=headers)
        try:
            check_link_status(self.url, 'api')
            raise pytest.fail('No exception occurred. Expected: InvalidContentType')
        except InvalidContentType as err:
            assert err.args[0] == 'application/text/json'

    @requests_mock.Mocker(kw='mock_request')
    def test_unsupported_content_type(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'video/mp4'}
        mock_request.head(self.url, headers=headers)
        try:
            check_link_status(self.url, 'api')
            raise pytest.fail('No exception occurred. Expected: UnsupportedContentType')
        except UnsupportedContentType as err:
            assert err.args[0] == 'Unsupported type: video/mp4'

    @requests_mock.Mocker(kw='mock_request')
    def test_check_link_status_no_errors(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'application/json'}
        mock_request.head(self.url, headers=headers)
        check_link_status(self.url, 'api')

    @requests_mock.Mocker(kw='mock_request')
    def test_check_link_status_use_get_method_without_errors(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'application/json'}
        mock_request.head(self.url, headers=headers, status_code=405)
        mock_request.get(self.url, headers=headers)
        check_link_status(self.url, 'api')

    @requests_mock.Mocker(kw='mock_request')
    def test_check_link_status_resource_location_changed(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'text/html', 'Location': 'http://redirect-mocker.com'}
        mock_request.head(self.url, headers=headers, status_code=301)
        mock_request.head('http://redirect-mocker.com', headers={'Content-Type': 'text/html'})
        try:
            check_link_status(self.url, 'website')
            raise pytest.fail('No exception occurred. Expected: InvalidResponseCode')
        except InvalidResponseCode as err:
            assert err.args[0] == 'Resource location has been moved!'


class TestDownloadFile:

    url = 'https://mocker-test.com'

    def test_throw_invalid_url(self):
        try:
            download_file('www.brokenlink')
            raise pytest.fail('No exception occurred. Expected: InvalidUrl')
        except InvalidUrl as err:
            assert err.args[0] == 'Invalid url address: www.brokenlink'

    @requests_mock.Mocker(kw='mock_request')
    def test_throw_invalid_url_scheme(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'application/json'}
        mock_request.get('http://mocker-test.com', headers=headers, status_code=504)
        try:
            download_file('http://mocker-test.com')
            raise pytest.fail('No exception occurred. Expected: InvalidScheme')
        except InvalidSchema as err:
            assert err.args[0] == 'Invalid schema!'

    @requests_mock.Mocker(kw='mock_request')
    def test_throw_invalid_response_code(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'application/json'}
        mock_request.get(self.url, headers=headers, status_code=504)
        try:
            download_file(self.url)
            raise pytest.fail('No exception occurred. Expected: InvalidResponseCode')
        except InvalidResponseCode as err:
            assert err.args[0] == 'Invalid response code: 504'

    @requests_mock.Mocker(kw='mock_request')
    def test_invalid_content_type(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'application/text/json'}
        mock_request.get(self.url, headers=headers)
        try:
            download_file(self.url)
            raise pytest.fail('No exception occurred. Expected: InvalidContentType')
        except InvalidContentType as err:
            assert err.args[0] == 'application/text/json'

    @requests_mock.Mocker(kw='mock_request')
    def test_unsupported_content_type(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'video/mp4'}
        mock_request.get(self.url, headers=headers)
        try:
            download_file(self.url)
            raise pytest.fail('No exception occurred. Expected: UnsupportedContentType')
        except UnsupportedContentType as err:
            assert err.args[0] == 'Unsupported type: video/mp4'

    @requests_mock.Mocker(kw='mock_request')
    def test_download_file_missing_content_type(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {}
        mock_request.get(self.url, headers=headers)
        try:
            download_file(self.url)
            raise pytest.fail('No exception occurred. Expected: MissingContentType')
        except MissingContentType as err:
            assert err.args == ()

    @requests_mock.Mocker(kw='mock_request')
    def test_download_file_filename_from_content_disposition(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'text/html', 'Content-Disposition': 'attachment; filename=example_file.html'}
        mock_request.get(self.url, headers=headers, content=b'')
        res_type, res_details = download_file(self.url)
        assert res_details['filename'] == 'example_file.html'

    @requests_mock.Mocker(kw='mock_request')
    def test_download_file_filename_from_content_disposition_with_additional_data(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'text/html',
                   'Content-Disposition': 'attachment; filename=example_file.html; size=1234'}
        mock_request.get(self.url, headers=headers, content=b'')
        res_type, res_details = download_file(self.url)
        assert res_details['filename'] == 'example_file.html'

    @requests_mock.Mocker(kw='mock_request')
    def test_download_file_is_octetstream(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'application/octetstream',
                   'Content-Disposition': 'attachment; filename=example_file.doc'}
        mock_request.get(self.url, headers=headers, content=b'')
        res_type, res_details = download_file(self.url)
        assert res_details['format'] == 'doc'

    @requests_mock.Mocker(kw='mock_request')
    def test_download_file_is_octetstream_from_content_disposition_with_additional_data(self, **kwargs):
        mock_request = kwargs['mock_request']
        headers = {'Content-Type': 'application/octetstream',
                   'Content-Disposition': 'attachment; filename="example_file.doc"; size=1234'}
        mock_request.get(self.url, headers=headers, content=b'')
        res_type, res_details = download_file(self.url)
        assert res_details['format'] == 'doc'


def test_content_type_from_file_format_unsupported_format():
    family, content_type = content_type_from_file_format('mp4')
    assert family is None
    assert content_type is None


def test_filename_from_url_extension_from_content_type():
    filename, extension = filename_from_url('http://mocker-test.com/test-file', 'video/mp4')
    assert filename == 'test-file'
    assert extension == 'mp4'


class TestResourceTypeDiscovery:

    def test__get_resource_type_recognize_xml_attachment_as_file(self, xml_resource_file_response):
        resource_type = _get_resource_type(xml_resource_file_response)
        assert resource_type == 'file'

    def test__get_resource_type_recognize_xml_non_attachment_as_api(self, xml_resource_api_response):
        resource_type = _get_resource_type(xml_resource_api_response)
        assert resource_type == 'api'

    def test__get_resource_type_recognize_json_as_api(self, json_resource_response):
        resource_type = _get_resource_type(json_resource_response)
        assert resource_type == 'api'

    def test__get_resource_type_recognize_jsonstat_as_api(self, jsonstat_resource_response):
        resource_type = _get_resource_type(jsonstat_resource_response)
        assert resource_type == 'api'

    def test__get_resource_type_recognize_html_as_web(self, html_resource_response):
        resource_type = _get_resource_type(html_resource_response)
        assert resource_type == 'website'
