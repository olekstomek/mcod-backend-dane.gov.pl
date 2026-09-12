Feature: Dataset Comment

  Scenario: Dataset comment recipients list contains email from update_notification_recipient_email attribute of related dataset
    Given dataset created with params {"id": 999, "update_notification_recipient_email": "update_notification_recipient_email@example.com"}
    When api request method is POST
    And api request path is /datasets/999/comments
    And api request dataset_comment data has {}
    And send api request and fetch the response
    Then latest datasetcomment attribute editor_email is update_notification_recipient_email@example.com
