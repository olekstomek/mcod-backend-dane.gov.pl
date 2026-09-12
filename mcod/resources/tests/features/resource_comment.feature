@elasticsearch
Feature: Resource Comment

  Scenario Outline: Valid resource comment
    Given resource with id 999
    When api request method is POST
    And api request path is /resources/999/comments
    And api request <object_type> data has <req_data>
    And send api request and fetch the response
    Then api's response status code is 201

    Examples:
    | object_type      | req_data                                                          |
    | resource_comment | {"comment": "some valid\ncomment"}                                |
    | resource_comment | {"comment": "123"}                                                |
    | resource_comment | {"comment": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"} |

  Scenario: Resource comment is required
    Given resource with id 999
    When api request method is POST
    And api request path is /resources/999/comments
    And api request resource_comment data has {}
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field errors/[0]/code is 422_unprocessable_entity
    And api's response body field errors/[0]/status is 422 Unprocessable Entity
    And api's response body field errors/[0]/source/pointer is /data/attributes/comment
    And api's response body field errors/[0]/detail is Brak danych w wymaganym polu.

  Scenario: Resource comment for removed resource
    Given removed resource with id 999
    When api request method is POST
    And api request path is /resources/999/comments
    And api request resource_comment data has {"comment": "some valid\ncomment"}
    And send api request and fetch the response
    Then api's response status code is 404
    And api's response body field errors/[0]/code is 404_not_found
    And api's response body field errors/[0]/status is 404 Not Found

  Scenario: Resource comment for draft resource
    Given draft resource with id 999
    When api request method is POST
    And api request path is /resources/999/comments
    And api request resource_comment data has {"comment": "some valid\ncomment"}
    And send api request and fetch the response
    Then api's response status code is 404
    And api's response body field errors/[0]/code is 404_not_found
    And api's response body field errors/[0]/status is 404 Not Found

  Scenario: Resource comment recipients list contains address from update_notification_recipient_email attribute of related dataset
    Given dataset with id 999 and update_notification_recipient_email is update_notification_recipient_email@example.com
    Given resource created with params {"id": 999, "dataset_id": 999}
    When api request method is POST
    And api request path is /resources/999/comments
    And api request resource_comment data has {"comment": "some valid\ncomment"}
    And send api request and fetch the response
    Then latest resourcecomment attribute editor_email is update_notification_recipient_email@example.com
