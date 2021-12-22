@elasticsearch
Feature: Showcases list API

  Scenario Outline: Showcase routes
    Given dataset with id 999
    And showcase created with params {"id": 999, "slug": "showcase-slug", "datasets": [999]}
    When api request method is GET
    And api request path is <request_path>
    Then send api request and fetch the response
    And api's response status code is 200
    Examples:
    | request_path                          |
    | /showcases                            |
    | /showcases/999                        |
    | /showcases/999,showcase-slug          |
    | /showcases/999/datasets               |
    | /showcases/999,showcase-slug/datasets |

  Scenario: Showcases list item returns slug in self link
    Given showcase created with params {"id": 999, "slug": "showcase-slug"}
    When api request method is GET
    And api request path is /showcases?id=999
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field data/[0]/links/self endswith 999,showcase-slug

  Scenario Outline: Showcases list is sortable by views_count
    Given 3 showcases
    When api request method is GET
    And api request path is <request_path>
    Then api request param <req_param_name> is <req_param_value>
    And send api request and fetch the response
    And api's response list is sorted by <sort> <sort_order>
    Examples:
    | request_path   | req_param_name | req_param_value | sort        | sort_order   |
    | /1.0/showcases | sort           | views_count     | views_count | ascendingly  |
    | /1.0/showcases | sort           | -views_count    | views_count | descendingly |
    | /1.4/showcases | sort           | views_count     | views_count | ascendingly  |
    | /1.4/showcases | sort           | -views_count    | views_count | descendingly |

  Scenario: Showcases list contains published showcases
    Given showcase created with params {"id": 999, "title": "Testowa innowacja", "status": "published"}
    When api request method is GET
    And api request path is /1.0/showcases?id=999
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field data/[0]/attributes/title is Testowa innowacja

  Scenario: Showcases list doesnt contains draft showcases
    Given showcase created with params {"id": 999, "title": "Testowa innowacja", "status": "draft"}
    When api request method is GET
    And api request path is /1.0/showcases?id=999
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field data/[0]/attributes/title does not contain Testowa innowacja

  Scenario: Created draft showcase with related datasets is not pushed into index (not visible in Search)
    Given dataset with id 999
    And showcase created with params {"id": 999, "title": "Testowa innowacja", "status": "draft", "datasets": [999]}
    When api request method is GET
    And api request path is /1.0/showcases?id=999
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field data/[0]/attributes/title does not contain Testowa innowacja

  Scenario: Featured showcases
    Given featured showcases
    When api request method is GET
    And api request path is /1.4/showcases
    And api request param is_featured is true
    Then send api request and fetch the response
    And api's response status code is 200
    And 4 featured showcases are returned
