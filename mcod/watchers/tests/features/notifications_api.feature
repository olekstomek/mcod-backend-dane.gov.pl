@elasticsearch
Feature: Notifications API
  Scenario: Notifications listing
    Given logged active user
    And article with id 1111
    And subscription with id 999 of article with id 1111 as art-1111
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 0
    And set title to my-title on article with id 1111
    And send api request and fetch the response
    And api's response body field /meta/count is 1
    And api's response status code is 200
    And api's response body field /data/0/attributes/status is new
    And api's response body field /data/0/attributes/notification_type is object_updated
    And api's response body field /data/0/type is notification
    And api's response body field /data/0/relationships/subscription/data/type is subscription
    And api's response body field /data/0/relationships/subscription/data/id is 999
    And api's response body field /data/0/relationships/subscribed_object/data/type is article
    And api's response body field /data/0/relationships/subscribed_object/data/id is 1111
    And api's response body field /meta/notifications/articles/new is 1
    And set status to draft on article with id 1111
    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response status code is 200
    And api's response body field /data/0/attributes/status is new
    And api's response body field /data/0/attributes/notification_type is object_removed
    And api's response body field /data/0/type is notification
    And api's response body field /data/0/relationships/subscription/data/type is subscription
    And api's response body field /data/0/relationships/subscription/data/id is 999
    And api's response body field /data/0/relationships/subscribed_object/data/type is article
    And api's response body field /data/0/relationships/subscribed_object/data/id is 1111
    And api's response body field /meta/notifications/articles/new is 2

  Scenario: Notification with id 999
    Given logged active user
    And article with id 888
    And subscription with id 999 of article with id 888 as article-888
    And notification with id 1000 for subscription with id 999
    When api request method is GET
    And api request path is /auth/notifications/1000
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/attributes/status is new
    And api's response body field /data/attributes/notification_type is object_updated
    And api's response body field /data/type is notification
    And api's response body field /data/id is 1000
    And api's response body field /data/relationships/subscription/data/type is subscription
    And api's response body field /data/relationships/subscription/data/id is 999
    And api's response body field /data/relationships/subscribed_object/data/type is article
    And api's response body field /data/relationships/subscribed_object/data/id is 888
    And api request path is /auth/subscriptions/999
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /data/relationships/notifications/meta/count is 1
    And api request path is /auth/subscriptions/999/notifications
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /meta/notifications/articles/new is 1

  Scenario: Notifications bulk update
    Given logged active user
    And article with id 888
    And subscription with id 999 of article with id 888 as article-888
    And second subscription with id 998 of application with id 887 as app-887
    And third subscription with id 997 of institution with id 777 as inst-777
    And notification with id 1000 for subscription with id 999
    And second notification with id 1001 for subscription with id 998
    And third notification with id 1002 for subscription with id 997
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 3
    And set slug to article-888-a on article with id 888
    And set slug to app-887-a on application with id 887
    And set slug to inst-777-a on institution with id 777
    And send api request and fetch the response
    And api's response body field /meta/count is 6
    And api's response status code is 200
    And api request method is PATCH
    And api request body field /data is of type list
    And api request body field /data/0 is of type dict
    And api request body field /data/1 is of type dict
    And api request body field /data/2 is of type dict
    And api request body field /data/0/type is notification
    And api request body field /data/0/id is 1000
    And api request body field /data/0/attributes/status is read
    And api request body field /data/1/type is notification
    And api request body field /data/1/id is 1001
    And api request body field /data/1/attributes/status is read
    And api request body field /data/2/type is notification
    And api request body field /data/2/id is 1002
    And api request body field /data/2/attributes/status is read
    And send api request and fetch the response
    And api's response status code is 202
    And api request method is GET
    And api request path is /auth/notifications?status=new
    And send api request and fetch the response
    And api's response body field /meta/count is 3
    And api's response status code is 200
    And api's response body field /data/*/attributes/status is new
    And api's response body field /data/*/id does not contain 1000
    And api's response body field /data/*/id does not contain 1001
    And api's response body field /data/*/id does not contain 1002
    And api request path is /auth/notifications?status=read
    And send api request and fetch the response
    And api's response body field /meta/count is 3
    And api's response status code is 200
    And api's response body field /data/*/attributes/status is read
    And api's response body field /data/*/id contains 1000
    And api's response body field /data/*/id contains 1001
    And api's response body field /data/*/id contains 1002
    And api's response body field /meta/notifications/articles/new is 1
    And api's response body field /meta/notifications/applications/new is 1
    And api's response body field /meta/notifications/institutions/new is 1

  Scenario: Notifications filtering
    Given logged active user
    And article with id 888
    And second article with id 887
    And another institution with id 777
    And subscription with id 999 of article with id 888 as article-888
    And second subscription with id 998 of article with id 887 as article-887
    And third subscription with id 997 of institution with id 777 as inst-777
    And notification with id 1000 for subscription with id 999
    And second notification with id 1001 for subscription with id 998
    And third notification with id 1002 for subscription with id 997
    When api request method is GET
    And api request path is /auth/notifications?object_name=article
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body field /data/*/relationships/subscribed_object/data/type is article
    And api request path is /auth/notifications?object_name=institution
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/*/relationships/subscribed_object/data/type is institution
    And api request path is /auth/notifications?object_name=dataset
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 0
    And api request path is /auth/notifications?object_name=article&object_id=888
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/0/relationships/subscribed_object/data/type is article
    And api's response body field /data/0/relationships/subscribed_object/data/id is 888
    And api's response body field /data/0/relationships/subscription/data/type is subscription
    And api's response body field /data/0/relationships/subscription/data/id is 999
    And api's response body field /data/0/id is 1000
    And api request path is /auth/notifications?object_name=article&object_id=888&status=read
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 0
    And api request path is /auth/notifications?object_name=article&object_id=888&status=new
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /meta/notifications/articles/new is 2
    And api's response body field /meta/notifications/institutions/new is 1

  Scenario: Remove notifications in bulk
    Given logged active user
    And article with id 888
    And second article with id 887
    And another institution with id 777
    And subscription with id 999 of article with id 888 as article-888
    And second subscription with id 998 of article with id 887 as article-887
    And third subscription with id 997 of institution with id 777 as inst-777
    And notification with id 1000 for subscription with id 999
    And second notification with id 1001 for subscription with id 998
    And third notification with id 1002 for subscription with id 997
    When api request method is DELETE
    And api request body field /data is of type list
    And api request body field /data/0 is of type dict
    And api request body field /data/1 is of type dict
    And api request body field /data/0/type is notification
    And api request body field /data/0/id is 1000
    And api request body field /data/1/type is notification
    And api request body field /data/1/id is 1002
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 202
    And api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/0/id is 1001

  Scenario: Single notification updating
    Given logged active user
    And article with id 888
    And second article with id 887
    And subscription with id 999 of article with id 888 as article-888
    And second subscription with id 998 of article with id 887 as article-887
    And notification with id 1000 for subscription with id 999
    And second notification with id 1001 for subscription with id 998
    When api request method is PATCH
    And api request path is /auth/notifications/1000
    And api request body field /data/type is notification
    And api request body field /data/id is 1000
    And api request body field /data/attributes/status is read
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/id is 1000
    And api's response body field /data/attributes/status is read
    And api's response body field /data/attributes/notification_type is object_updated
    And api's response body field /data/type is notification
    And api's response body field /data/relationships/subscription/data/type is subscription
    And api's response body field /data/relationships/subscription/data/id is 999
    And api's response body field /data/relationships/subscribed_object/data/type is article
    And api's response body field /data/relationships/subscribed_object/data/id is 888
    And api request path is /auth/notifications
    And api request method is GET
    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response body field /data/1/id is 1000
    And api's response body field /data/1/attributes/status is read
    And api's response body field /data/1/attributes/notification_type is object_updated
    And api's response body field /data/1/type is notification
    And api's response body field /data/1/relationships/subscription/data/type is subscription
    And api's response body field /data/1/relationships/subscription/data/id is 999
    And api's response body field /data/1/relationships/subscribed_object/data/type is article
    And api's response body field /data/1/relationships/subscribed_object/data/id is 888
    And api's response body field /data/0/id is 1001
    And api's response body field /data/0/attributes/status is new

  Scenario: Single notification removing
    Given logged active user
    And article with id 888
    And second article with id 887
    And subscription with id 999 of article with id 888 as article-888
    And second subscription with id 998 of article with id 887 as article-887
    And notification with id 1000 for subscription with id 999
    And second notification with id 1001 for subscription with id 998
    When api request method is DELETE
    And api request path is /auth/notifications/1000
    And send api request and fetch the response
    Then api's response status code is 204
    And api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    And api's response body field /meta/count is 1
    And api's response body field /data/0/id is 1001
    And api's response body field /data/0/attributes/status is new
    And api request path is /auth/notifications/1000
    And send api request and fetch the response
    Then api's response status code is 404

  Scenario: Included
    Given logged active user
    And article with id 888
    And another application with id 887
    And subscription with id 999 of article with id 888 as article-888
    And second subscription with id 998 of application with id 887 as application-887
    And notification with id 1000 for subscription with id 999
    And second notification with id 1001 for subscription with id 998
    And third notification with id 1002 for subscription with id 998
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 3
    And size of api's response body field /included is 2
    And api's response body field /included/*/type contains application
    And api's response body field /included/*/type contains article
    And api's response body field /included/*/id startswith 888
    And api's response body field /included/*/id startswith 887
    And api request path is /auth/subscriptions/998/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2
    And size of api's response body field /included is 1
    And api's response body field /included/0/type contains application
    And api's response body field /included/0/id startswith 887
    And api request path is /auth/notifications/1000
    And send api request and fetch the response
    Then api's response status code is 200
    And size of api's response body field /included is 1
    And api's response body field /included/0/type is article
    And api's response body field /included/0/id startswith 888

  Scenario: Notification type related_object_publicated
    Given logged active user
    And article with id 888
    And dataset with id 900
    And subscription with id 999 of article with id 888 as article-888
    And add dataset with id 900 to article with id 888
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/0/attributes/status is new
    And api's response body field /data/0/attributes/notification_type is related_object_publicated

  Scenario: Notification type related_object_removed (soft remove)
    Given logged active user
    And dataset with id 900
    And article with id 888
    And add dataset with id 900 to article with id 888
    And subscription with id 999 of article with id 888 as article-888
    And remove dataset with id 900
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/0/attributes/status is new
    And api's response body field /data/0/attributes/notification_type is related_object_removed

  Scenario: Notification type related_object_removed (m2m remove)
    Given logged active user
    And dataset with id 900
    And article with id 888
    And add dataset with id 900 to article with id 888
    And subscription with id 999 of article with id 888 as article-888
    And remove dataset with id 900 from article with id 888
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/0/attributes/status is new
    And api's response body field /data/0/attributes/notification_type is related_object_removed

  Scenario: Notification type related_object_restored
    Given logged active user
    And dataset with id 900
    And article with id 888
    And add dataset with id 900 to article with id 888
    And remove dataset with id 900
    And subscription with id 999 of article with id 888 as article-888
    And restore dataset with id 900
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/0/attributes/status is new
    And api's response body field /data/0/attributes/notification_type is related_object_restored

  Scenario: Notification type related_object_updated
    Given logged active user
    And dataset with id 900
    And article with id 888
    And add dataset with id 900 to article with id 888
    And subscription with id 999 of article with id 888 as article-888
    And set title to changed-title on dataset with id 900
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/0/attributes/status is new
    And api's response body field /data/0/attributes/notification_type is related_object_updated

  Scenario: Notification type related_object_restored
    Given logged active user
    And dataset with id 900
    And article with id 888
    And another application with id 777
    And second institution with id 666
    And subscription with id 999 of article with id 888 as article-888
    And second subscription with id 998 of dataset with id 900 as dataset-900
    And third subscription with id 997 of application with id 777 as app-777
    And fourth subscription with id 996 of institution with id 666 as inst-666
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 0
    And remove dataset with id 900
    And remove article with id 888
    And remove application with id 777
    And remove institution with id 666
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 4
    And api's response body field /data/*/attributes/status is new
    And api's response body field /data/*/attributes/notification_type is object_removed
    And restore dataset with id 900
    And restore article with id 888
    And restore application with id 777
    And restore institution with id 666
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 8
    And api's response body field /data/*/attributes/status is new
    And api's response body field /data/0/attributes/notification_type is object_restored
    And api's response body field /data/1/attributes/notification_type is object_restored
    And api's response body field /data/2/attributes/notification_type is object_restored
    And api's response body field /data/3/attributes/notification_type is object_restored
    And api's response body field /data/4/attributes/notification_type is object_removed
    And api's response body field /data/5/attributes/notification_type is object_removed
    And api's response body field /data/6/attributes/notification_type is object_removed
    And api's response body field /data/7/attributes/notification_type is object_removed

  Scenario: Notification type related_object_publicated
    Given logged active user
    And dataset with id 900
    And article with id 888
    And subscription with id 999 of article with id 888 as article-888
    And add dataset with id 900 to article with id 888
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/0/attributes/status is new
    And api's response body field /data/0/attributes/notification_type is related_object_publicated

  Scenario: Notification type object_restored (soft_remove)
    Given logged active user
    And application with id 900
    And article with id 888
    And subscription with id 999 of article with id 888 as article-888
    And second subscription with id 998 of application with id 900 as app-900
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 0
    And remove application with id 900
    And remove article with id 888
    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response body field /data/*/attributes/notification_type is object_removed
    And restore article with id 888
    And restore application with id 900
    And send api request and fetch the response
    And api's response body field /meta/count is 4
    And api's response body field /data/0/attributes/notification_type is object_restored
    And api's response body field /data/1/attributes/notification_type is object_restored
    And api's response body field /data/2/attributes/notification_type is object_removed
    And api's response body field /data/3/attributes/notification_type is object_removed

  Scenario: Notification type object_restored (status chage)
    Given logged active user
    And application with id 900
    And article with id 888
    And subscription with id 999 of article with id 888 as article-888
    And second subscription with id 998 of application with id 900 as app-900
    When api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 0
    And set status to draft on application with id 900
    And set status to draft on article with id 888
    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response body field /data/*/attributes/notification_type is object_removed
    And set status to published on application with id 900
    And set status to published on article with id 888
    And send api request and fetch the response
    And api's response body field /meta/count is 4
    And api's response body field /data/0/attributes/notification_type is object_restored
    And api's response body field /data/1/attributes/notification_type is object_restored
    And api's response body field /data/2/attributes/notification_type is object_removed
    And api's response body field /data/3/attributes/notification_type is object_removed

  Scenario: Change notifications status
    Given logged active user
    And article with id 888
    And second article with id 887
    And another institution with id 777
    And subscription with id 999 of article with id 888 as article-888
    And second subscription with id 998 of article with id 887 as article-887
    And third subscription with id 997 of institution with id 777 as inst-777
    And notification with id 1000 for subscription with id 999
    And second notification with id 1001 for subscription with id 998
    And third notification with id 1002 for subscription with id 997
    When api request method is DELETE
    And api request path is /auth/notifications/status
    And send api request and fetch the response
    Then api's response status code is 202
    And api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 3
    And api's response body field /data/*/attributes/status is read
    And api request path is /auth/notifications/status
    And api request method is PATCH
    And send api request and fetch the response
    Then api's response status code is 202
    And api request path is /auth/notifications
    And api request method is GET
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 3
    And api's response body field /data/*/attributes/status is new
