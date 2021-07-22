@elasticsearch
Feature: History list API

  Scenario Outline: History list endpoint returns required data
    Given 3 histories
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field data/*/type is history
    And api's response body field data/*/attributes has fields action,change_user_id,change_timestamp,difference,message,new_value,row_id,table_name

    Examples:
    | request_path    |
    | /1.0/histories/ |
    | /1.4/histories/ |

  Scenario Outline: History list endpoint is filtered by id
    Given history with id 999
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response data has length 1
    And api's response body field data/[0]/id is 999
    And api's response body field data/[0]/attributes has fields action,change_user_id,change_timestamp,difference,message,new_value,row_id,table_name

    Examples:
    | request_path           |
    | /1.0/histories/?id=999 |
    | /1.4/histories/?id=999 |
