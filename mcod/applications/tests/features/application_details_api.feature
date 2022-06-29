@elasticsearch
Feature: Application details API

  Scenario: Applications details item returns slug in self link
    Given application created with params {"id": 999, "slug": "application-slug"}
    When api request path is /applications/999
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field data/links/self endswith 999,application-slug

  Scenario Outline: Published application details endpoint is available
    Given application with id 999
    When api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    Examples:
    | request_path           |
    | /1.0/applications/999/ |
    | /1.4/applications/999/ |

  Scenario Outline: Draft application details endpoint is not available for editor in API 1.0
    Given draft application with id 999
    And logged editor user
    When api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 404
    Examples:
    | request_path |
    | /1.0/applications/999/ |
    | /1.4/applications/999/ |

  Scenario Outline: Test draft application details endpoint is available for admin (preview)
    Given draft application with id 999
    And logged admin user
    When api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    Examples:
    | request_path           |
    | /1.0/applications/999/ |
    | /1.4/applications/999/ |

  Scenario: Test application datasets contains valid links to related items
    Given application with id 999 and 3 datasets
    When api request path is /1.4/applications/999/datasets
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response datasets contain valid links to related resources
