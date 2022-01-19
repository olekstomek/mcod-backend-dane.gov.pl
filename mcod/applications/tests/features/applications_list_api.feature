@elasticsearch
Feature: Applications list API

  Scenario Outline: Application routes
    Given dataset with id 999
    And application created with params {"id": 999, "slug": "application-slug", "datasets": [999]}
    When api request method is GET
    And api request path is <request_path>
    Then send api request and fetch the response
    And api's response status code is 200
    Examples:
    | request_path                                |
    | /applications                               |
    | /applications/999                           |
    | /applications/999,application-slug          |
    | /applications/999/datasets                  |
    | /applications/999,application-slug/datasets |

  Scenario: Applications list item returns slug in self link
    Given application created with params {"id": 999, "slug": "application-slug"}
    When api request method is GET
    And api request path is /applications?id=999
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field data/[0]/links/self endswith 999,application-slug

  Scenario Outline: Applications list is sortable by views_count
    Given 3 applications
    When api request method is GET
    And api request path is <request_path>
    Then api request param <req_param_name> is <req_param_value>
    And send api request and fetch the response
    And api's response list is sorted by <sort> <sort_order>
    And api's response body has field data/*/relationships/datasets/meta/count
    And api's response body has field data/*/relationships/datasets/links/related
    Examples:
    | request_path      | req_param_name | req_param_value | sort        | sort_order   |
    | /1.0/applications | sort           | views_count     | views_count | ascendingly  |
    | /1.0/applications | sort           | -views_count    | views_count | descendingly |
    | /1.4/applications | sort           | views_count     | views_count | ascendingly  |
    | /1.4/applications | sort           | -views_count    | views_count | descendingly |

  Scenario: Applications list contains published applications
    Given application created with params {"id": 999, "title": "Testowa aplikacja", "status": "published"}
    When api request method is GET
    And api request path is /1.0/applications?id=999
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field data/[0]/attributes/title is Testowa aplikacja

  Scenario: Applications list doesnt contains draft applications
    Given application created with params {"id": 999, "title": "Testowa aplikacja", "status": "draft"}
    When api request method is GET
    And api request path is /1.0/applications?id=999
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field data/[0]/attributes/title does not contain Testowa aplikacja

  Scenario: Created draft application with related datasets is not pushed into index (not visible in Search)
    Given dataset with id 999
    And application created with params {"id": 999, "title": "Testowa aplikacja", "status": "draft", "datasets": [999]}
    When api request method is GET
    And api request path is /1.0/applications?id=999
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field data/[0]/attributes/title does not contain Testowa aplikacja
