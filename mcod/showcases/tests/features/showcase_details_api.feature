@elasticsearch
Feature: Showcase details API

  Scenario: Showcases details item returns slug in self link
    Given showcase created with params {"id": 999, "slug": "showcase-slug"}
    When api request method is GET
    And api request path is /showcases/999
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field data/links/self endswith 999,showcase-slug

  Scenario Outline: Published showcase details endpoint is available
    Given showcase with id 999
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    Examples:
    | request_path        |
    | /1.0/showcases/999/ |
    | /1.4/showcases/999/ |

  Scenario Outline: Draft showcase details endpoint is not available for editor
    Given draft showcase with id 999
    And logged editor user
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 404
    Examples:
    | request_path        |
    | /1.0/showcases/999/ |
    | /1.4/showcases/999/ |

  Scenario Outline: Test draft showcase details endpoint is available for admin (preview)
    Given draft showcase with id 999
    And logged admin user
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    Examples:
    | request_path        |
    | /1.0/showcases/999/ |
    | /1.4/showcases/999/ |

  Scenario: Test showcase datasets contains valid links to related items
    Given showcase with id 999 and 3 datasets
    When api request method is GET
    And api request path is /1.4/showcases/999/datasets
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response datasets contain valid links to related resources
