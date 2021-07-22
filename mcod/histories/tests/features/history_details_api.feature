@elasticsearch
Feature: History details API

  Scenario Outline: History details endpoint returns required data
    # TODO: how to create history object? (some errors related to table_schema during creation).
    Given history with id 999
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field data/type is history
    And api's response body field data/id is 999
    And api's response body field data/attributes has fields action,change_user_id,change_timestamp,difference,message,new_value,row_id,table_name

    Examples:
    | request_path        |
    | /1.0/histories/999/ |
    | /1.4/histories/999/ |
