@elasticsearch
Feature: Query Watcher
  Scenario: query watcher updates
    Given logged active user
    And article with id 888
    And 6 random instances of article
    And query subscription with id 999 for url http://localhost:8000/articles as my-articles
    When api request method is GET
    And api request path is /auth/subscriptions/999
    And send api request and fetch the response
    Then api's response status code is 200
    And api request path is /auth/notifications
    And send api request and fetch the response
    And api's response body field /meta/count is 0
    And 6 random instances of article
    And trigger query watcher update
    And send api request and fetch the response
    And api's response body field /meta/count is 1
    And api's response body field /data/0/attributes/notification_type is result_count_incresed
    And api's response body field /data/0/attributes/ref_value is 13
    And api's response body field /data/*/relationships/subscribed_object/data/id is http://localhost:8000/articles
    And api's response body field /data/*/relationships/subscribed_object/data/type is query
    And remove article with id 888
    And trigger query watcher update
    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response body field /data/0/attributes/notification_type is result_count_decresed
    And api's response body field /data/0/attributes/ref_value is 12
    And api's response body field /data/1/attributes/notification_type is result_count_incresed
    And api's response body field /data/1/attributes/ref_value is 13
    And api's response body field /data/*/relationships/subscribed_object/data/id is http://localhost:8000/articles
    And api's response body field /data/*/relationships/subscribed_object/data/type is query
    And restore article with id 888
    And trigger query watcher update
    And send api request and fetch the response
    And api's response body field /meta/count is 3
    And api's response body field /data/0/attributes/notification_type is result_count_incresed
    And api's response body field /data/0/attributes/ref_value is 13
    And api's response body field /data/1/attributes/notification_type is result_count_decresed
    And api's response body field /data/1/attributes/ref_value is 12
    And api's response body field /data/2/attributes/notification_type is result_count_incresed
    And api's response body field /data/2/attributes/ref_value is 13
    And api's response body field /data/*/relationships/subscribed_object/data/id is http://localhost:8000/articles
    And api's response body field /data/*/relationships/subscribed_object/data/type is query
