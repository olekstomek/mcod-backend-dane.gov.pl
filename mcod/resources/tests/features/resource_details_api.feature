@elasticsearch
Feature: Resource details API

  Scenario: Test resource details endpoint increments popularity of the resource in API 1.4
    Given resource with id 998 and views_count is 0
    When api request method is GET
    And api request header x-api-version is 1.0
    And api request path is /1.4/resources/998/
    And send api request and fetch the response
    Then api's response status code is 200
    And counter incrementing task is executed
    And resource with id 998 views_count is 1

  Scenario: Test unpublished resource details endpoint doesnt increment popularity of the resource in API 1.4
    Given unpublished resource with id 999 and views_count is 0
    When api request method is GET
    And api request path is /1.4/resources/999/
    And send api request and fetch the response
    Then api's response status code is 404
    And counter incrementing task is executed
    And resource with id 999 views_count is 0

  Scenario: Downloading endpoint increases download count
    Given resource with id 999 and downloads_count is 0
    When api request method is GET
    And api request header x-api-version is 1.0
    And api request path is /1.0/resources/999/file
    And send api request and fetch the response
    Then api's response status code is 302
    And counter incrementing task is executed
    And resource with id 999 downloads_count is 1

  Scenario: Trying to download unpublished resource doesnt increase download count
    Given unpublished resource with id 999 and downloads_count is 0
    When api request method is GET
    And api request header x-api-version is 1.0
    And api request path is /1.4/resources/999/file
    And send api request and fetch the response
    Then api's response status code is 404
    And counter incrementing task is executed
    And resource with id 999 downloads_count is 0

  Scenario: Test resource details endpoint does not contain included section by default in API 1.4
    Given resource with id 999 and views_count is 0
    When api request method is GET
    And api request path is /1.4/resources/999/
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body has no field included

  Scenario Outline: Test resource details contains resource ident in links section in API 1.4
    Given resource with id 999 and slug is resource-test-slug
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/links/self endswith 999,resource-test-slug

    Examples:
    | request_path                           |
    | /resources/999/                        |
    | /resources/999,resource-test-slug/     |
    | /1.4/resources/999/                    |
    | /1.4/resources/999,resource-test-slug/ |

  Scenario: Test resource details endpoint contains included section in API 1.4
    Given resource with id 999 and views_count is 0
    When api request method is GET
    And api request path is /1.4/resources/999/
    Then api request param include is dataset
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body has field included

  Scenario: Test resource details endpoint for xls resource converted to csv
    Given resource with id 1001 and xls file converted to csv
    When api request method is GET
    And api request path is /1.4/resources/1001/
    And send api request and fetch the response
    Then api's response body field data/attributes/file_url endswith example_xls_file.xls
    And api's response body field data/attributes/csv_file_url endswith example_xls_file.csv
    And api's response body field data/attributes/csv_file_size is not None
    And api's response body field data/attributes/csv_download_url is not None

  Scenario: Test resource details endpoint for csv resource converted to jsonld
    Given resource with csv file converted to jsonld with params {"id": 999}
    When api request method is GET
    And api request path is /1.4/resources/999/
    And send api request and fetch the response
    Then api's response body field data/attributes/file_url endswith csv2jsonld.csv
    And api's response body field data/attributes/jsonld_file_url endswith csv2jsonld.jsonld
    And api's response body field data/attributes/jsonld_file_size is not None
    And api's response body field data/attributes/jsonld_download_url is not None
    And api's response body field data/attributes/openness_score is 4

  Scenario: Resource without regions has poland shown as region
    Given resource with id 999
    When api request method is GET
    And api request path is /1.4/resources/999/
    And send api request and fetch the response
    Then api's response body field data/attributes/regions/0/name is Polska
    And api's response body field data/attributes/regions/0/region_id is 85633723

  Scenario: Resource's region is returned by api
    Given dataset with id 998
    And resource with id 999 dataset id 998 and single main region
    When api request method is GET
    And api request path is /1.4/resources/999/
    And send api request and fetch the response
    Then api's response body field data/attributes/regions/0/name is Warszawa
    And api's response body field data/attributes/regions/0/region_id is 101752777
