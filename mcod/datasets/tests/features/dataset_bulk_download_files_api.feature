Feature: Dataset's bulk files download api

  Scenario: Dataset's resources archived files are possible to download and downloading then increases resources downloads counter
    Given dataset with id 1003
    And resource with csv file converted to jsonld with params {"id": 1001, "dataset_id": 1003, "downloads_count": 0, "title": "title_with_underline_"}
    And resource with csv file converted to jsonld with params {"id": 1002, "dataset_id": 1003, "downloads_count": 0, "title": "title_2_with_underline_"}
    When api request path is /1.4/datasets/1003/resources/files/download
    And json api validation is skipped
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response data has zipped 4 files
    And counter incrementing task is executed
    And resource with id 1001 downloads_count is 2
    And resource with id 1002 downloads_count is 2

  Scenario: Bulk download api returns 404 when dataset has no archive
    Given dataset with id 1004
    When api request path is /1.4/datasets/1004/resources/files/download
    And json api validation is skipped
    Then send api request and fetch the response
    And api's response status code is 404