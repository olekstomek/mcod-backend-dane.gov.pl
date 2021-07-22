@elasticsearch
Feature: Resource details API
  Scenario: Test resource details endpoint increments popularity of the resource in API 1.0
    Given resource with id 999 and views_count is 0
    When api request method is GET
    And api request path is /1.0/resources/999/
    And send api request and fetch the response
    Then api's response status code is 200
    # And counter incrementing task is executed
    # And resource with id 999 views_count is 1

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
    Given resource with id 999 and xls file converted to csv
    When api request method is GET
    And api request path is /1.4/resources/999/
    And send api request and fetch the response
    Then api's response body field data/attributes/file_url endswith example_xls_file.xls
    And api's response body field data/attributes/csv_file_url endswith example_xls_file.csv
    And api's response body field data/attributes/csv_file_size is not None
    And api's response body field data/attributes/csv_download_url is not None
