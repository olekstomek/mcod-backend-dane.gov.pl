@elasticsearch
Feature: Organizations API

  Scenario Outline: Filtering institutions by type
    Given institutions of type {"local": 3, "state": 3, "other": 3}
    When api request method is GET
    And api request path is <request_path>
    Then api request param <req_param_name> is <req_param_value>
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field <resp_body_field> is <resp_body_value>

    Examples:
    | request_path       | req_param_name | req_param_value | resp_body_field                      | resp_body_value |
    | /1.0/institutions/ | type           | local           | /data/*/attributes/institution_type  | local           |
    | /1.0/institutions/ | type           | state           | /data/*/attributes/institution_type  | state           |
    | /1.0/institutions/ | type           | other           | /data/*/attributes/institution_type  | other           |

    | /1.4/institutions/ | type           | local           | /data/*/attributes/institution_type  | local           |
    | /1.4/institutions/ | type           | state           | /data/*/attributes/institution_type  | state           |
    | /1.4/institutions/ | type           | other           | /data/*/attributes/institution_type  | other           |

  Scenario Outline: Institution on list contains required fields
    Given 3 institutions
    When api request method is GET
    And api request path is <request_path>
    Then send api request and fetch the response
    And api's response body has field /data/*/attributes/abbreviation
    And api's response body has field /data/*/attributes/datasets_count
    And api's response body has field /data/*/attributes/description
    And api's response body has field /data/*/attributes/notes
    And api's response body has field /data/*/attributes/resources_count
    And api's response body has field /data/*/attributes/sources

    Examples:
    | request_path       |
    | /1.0/institutions/ |
    | /1.4/institutions/ |
