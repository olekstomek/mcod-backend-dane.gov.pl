@elasticsearch
Feature: Notifications API
  Scenario: Notifications listing
    Given logged active user
    And subscription with id 2000 of dataset with id 1000 as dataset-1000

    When api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 0

    And set title to my-title on dataset with id 1000

    And send api request and fetch the response
    And api's response body field /meta/count is 1
    And api's response status code is 200
    And api's response body field /data/0/attributes/status is new
    And api's response body field /data/0/attributes/notification_type is object_updated
    And api's response body field /data/0/type is notification
    And api's response body field /data/0/relationships/subscription/data/type is subscription
    And api's response body field /data/0/relationships/subscription/data/id is 2000
    And api's response body field /data/0/relationships/subscribed_object/data/type is dataset
    And api's response body field /data/0/relationships/subscribed_object/data/id is 1000
    And api's response body field /meta/notifications/datasets/new is 1

    And set status to draft on dataset with id 1000

    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response status code is 200
    And api's response body field /data/0/attributes/status is new
    And api's response body field /data/0/attributes/notification_type is object_removed
    And api's response body field /data/0/type is notification
    And api's response body field /data/0/relationships/subscription/data/type is subscription
    And api's response body field /data/0/relationships/subscription/data/id is 2000
    And api's response body field /data/0/relationships/subscribed_object/data/type is dataset
    And api's response body field /data/0/relationships/subscribed_object/data/id is 1000
    And api's response body field /meta/notifications/datasets/new is 2


  Scenario: Notifications bulk update
    Given logged active user
    And subscription with id 2001 of dataset with id 1001 as dataset-1001
    And second subscription with id 2002 of dataset with id 1002 as dataset-1002

    And notification with id 3000 for subscription with id 2001
    And second notification with id 3001 for subscription with id 2002

    When api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2

    And set title to dataset-1001-a on dataset with id 1001

    And send api request and fetch the response
    And api's response body field /meta/count is 3
    And api's response status code is 200
    And api request method is PATCH
    And api request body field /data is of type list
    And api request body field /data/0 is of type dict
    And api request body field /data/0/type is notification
    And api request body field /data/0/id is 3000
    And api request body field /data/0/attributes/status is read
    And api request body field /data/1 is of type dict
    And api request body field /data/1/type is notification
    And api request body field /data/1/id is 3001
    And api request body field /data/1/attributes/status is read

    And send api request and fetch the response
    And api's response status code is 202
    And api request method is GET
    And api request path is /auth/notifications?status=new
    And send api request and fetch the response
    And api's response body field /meta/count is 1
    And api's response status code is 200
    And api's response body field /data/*/attributes/status is new
    And api's response body field /data/*/id does not contain 3000
    And api's response body field /data/*/id does not contain 3001
    And api request path is /auth/notifications?status=read
    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response status code is 200
    And api's response body field /data/*/attributes/status is read
    And api's response body field /data/*/id contains 3000
    And api's response body field /data/*/id contains 3001


  Scenario: Notifications filtering
    Given logged active user
    And subscription with id 2003 of dataset with id 1003 as dataset-1003
    And notification with id 3002 for subscription with id 2003

    When api request path is /auth/notifications?object_name=dataset
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/*/relationships/subscribed_object/data/type is dataset

    And api request path is /auth/notifications?object_name=institution
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 0

    And api request path is /auth/notifications?object_name=article
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 0

    And api request path is /auth/notifications?object_name=dataset&object_id=1003
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/0/relationships/subscribed_object/data/type is dataset
    And api's response body field /data/0/relationships/subscribed_object/data/id is 1003
    And api's response body field /data/0/relationships/subscription/data/type is subscription
    And api's response body field /data/0/relationships/subscription/data/id is 2003
    And api's response body field /data/0/id is 3002

    And api request path is /auth/notifications?object_name=dataset&object_id=1003&status=read
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 0

    And api request path is /auth/notifications?object_name=dataset&object_id=1003&status=new
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /meta/notifications/datasets/new is 1


  Scenario: Included
    Given logged active user
    And subscription with id 2004 of dataset with id 1004 as dataset-1004
    And second subscription with id 2005 of dataset with id 1005 as dataset-1005
    And notification with id 3003 for subscription with id 2004
    And second notification with id 3004 for subscription with id 2005
    And third notification with id 3005 for subscription with id 2005

    When api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 3
    And size of api's response body field /included is 2
    And api's response body field /included/*/type contains dataset
    And api's response body field /included/*/type contains dataset
    And api's response body field /included/*/id startswith 1004
    And api's response body field /included/*/id startswith 1005

    And api request path is /auth/subscriptions/2005/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2
    And size of api's response body field /included is 1
    And api's response body field /included/0/type contains dataset
    And api's response body field /included/0/id startswith 1005


  Scenario: Notification type object_restored (soft_remove)
    Given logged active user
    And subscription with id 2006 of dataset with id 1006 as dataset-1006
    And second subscription with id 2007 of dataset with id 1007 as dataset-1007

    When api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 0

    And remove dataset with id 1006
    And remove dataset with id 1007

    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response body field /data/*/attributes/notification_type is object_removed

    And restore dataset with id 1006
    And restore dataset with id 1007

    And send api request and fetch the response
    And api's response body field /meta/count is 4
    And api's response body field /data/0/attributes/notification_type is object_restored
    And api's response body field /data/1/attributes/notification_type is object_restored
    And api's response body field /data/2/attributes/notification_type is object_removed
    And api's response body field /data/3/attributes/notification_type is object_removed


  Scenario: Notification type object_restored (status chage)
    Given logged active user
    And subscription with id 2008 of dataset with id 1008 as dataset-1008
    And second subscription with id 2009 of dataset with id 1009 as dataset-1009

    When api request path is /auth/notifications
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 0

    And set status to draft on dataset with id 1008
    And set status to draft on dataset with id 1009

    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response body field /data/*/attributes/notification_type is object_removed

    And set status to published on dataset with id 1008
    And set status to published on dataset with id 1009

    And send api request and fetch the response
    And api's response body field /meta/count is 4
    And api's response body field /data/0/attributes/notification_type is object_restored
    And api's response body field /data/1/attributes/notification_type is object_restored
    And api's response body field /data/2/attributes/notification_type is object_removed
    And api's response body field /data/3/attributes/notification_type is object_removed


  Scenario: Change notifications status
    Given logged active user

    And subscription with id 2010 of dataset with id 1010 as dataset-1010
    And second subscription with id 2011 of dataset with id 1011 as dataset-1011
    And notification with id 3006 for subscription with id 2010
    And second notification with id 3007 for subscription with id 2011

    When api request method is DELETE
    And api request path is /auth/notifications/status
    And send api request and fetch the response
    Then api's response status code is 202

    And api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body field /data/*/attributes/status is read

    And api request path is /auth/notifications/status
    And api request method is PATCH
    And send api request and fetch the response
    Then api's response status code is 202

    And api request path is /auth/notifications
    And api request method is GET
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body field /data/*/attributes/status is new


  Scenario: Remove notifications in bulk
    Given logged active user
    And subscription with id 2012 of dataset with id 1012 as dataset-1012
    And second subscription with id 2013 of dataset with id 1013 as dataset-1013
    And third subscription with id 2014 of dataset with id 1014 as dataset-1014
    And notification with id 3008 for subscription with id 2012
    And second notification with id 3009 for subscription with id 2013
    And third notification with id 3010 for subscription with id 2014

    When api request method is DELETE
    And api request path is /auth/notifications
    And api request body field /data is of type list
    And api request body field /data/0 is of type dict
    And api request body field /data/1 is of type dict
    And api request body field /data/0/type is notification
    And api request body field /data/0/id is 3008
    And api request body field /data/1/type is notification
    And api request body field /data/1/id is 3009
    And send api request and fetch the response
    Then api's response status code is 202

    And api request method is GET
    And api request path is /auth/notifications
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/0/id is 3010


#  TODO refactor below tests to use Dataset <-> Resource relation in notifications once it's working
#  Scenario: Notification type related_object_restored
#    Given logged active user
#    And dataset with id 900
#    And article with id 1112
#    And add dataset with id 900 to article with id 1112
#
#    And remove dataset with id 900
#    And subscription with id 999 of article with id 1112 as article-1112
#    And restore dataset with id 900
#
#    When api request method is GET
#    And api request path is /auth/notifications
#    And send api request and fetch the response
#    Then api's response status code is 200
#    And api's response body field /meta/count is 1
#    And api's response body field /data/0/attributes/status is new
#    And api's response body field /data/0/attributes/notification_type is related_object_restored

# TEN SAM TEST PRZEPISANY DLA RELACJI Resource <-> Dataset NIE PRZECHODZI
#  Scenario: Notification type related_object_restored
#    Given logged active user
#    And dataset with id 900
#    And resource with id 3000 and dataset_id is 900
#
#    And remove resource with id 3000
#    And subscription with id 999 of dataset with id 900 as dataset-900
#    And restore resource with id 3000
#
#    When api request method is GET
#    And api request path is /auth/notifications
#    And send api request and fetch the response
#    Then api's response status code is 200
#    And api's response body field /meta/count is 1
#    And api's response body field /data/0/attributes/status is new
#    And api's response body field /data/0/attributes/notification_type is related_object_restored

#  Scenario: Notification type related_object_publicated
#    Given logged active user
#    And article with id 1112
#    And dataset with id 900
#    And subscription with id 999 of article with id 1112 as article-1112
#    And add dataset with id 900 to article with id 1112
#    When api request method is GET
#    And api request path is /auth/notifications
#    And send api request and fetch the response
#    Then api's response status code is 200
#    And api's response body field /meta/count is 1
#    And api's response body field /data/0/attributes/status is new
#    And api's response body field /data/0/attributes/notification_type is related_object_publicated
#
#
#  Scenario: Notification type related_object_removed (soft remove)
#    Given logged active user
#    And dataset with id 900
#    And article with id 1112
#    And add dataset with id 900 to article with id 1112
#    And subscription with id 999 of article with id 1112 as article-1112
#    And remove dataset with id 900
#    When api request method is GET
#    And api request path is /auth/notifications
#    And send api request and fetch the response
#    Then api's response status code is 200
#    And api's response body field /meta/count is 1
#    And api's response body field /data/0/attributes/status is new
#    And api's response body field /data/0/attributes/notification_type is related_object_removed
#
#
#  Scenario: Notification type related_object_removed (m2m remove)
#    Given logged active user
#    And dataset with id 900
#    And article with id 1112
#    And add dataset with id 900 to article with id 1112
#    And subscription with id 999 of article with id 1112 as article-1112
#    And remove dataset with id 900 from article with id 1112
#    When api request method is GET
#    And api request path is /auth/notifications
#    And send api request and fetch the response
#    Then api's response status code is 200
#    And api's response body field /meta/count is 1
#    And api's response body field /data/0/attributes/status is new
#    And api's response body field /data/0/attributes/notification_type is related_object_removed
#
#
#  Scenario: Notification type related_object_updated
#    Given logged active user
#    And dataset with id 900
#    And article with id 1112
#    And add dataset with id 900 to article with id 1112
#    And subscription with id 999 of article with id 1112 as article-1112
#    And set title to changed-title on dataset with id 900
#    When api request method is GET
#    And api request path is /auth/notifications
#    And send api request and fetch the response
#    Then api's response status code is 200
#    And api's response body field /meta/count is 1
#    And api's response body field /data/0/attributes/status is new
#    And api's response body field /data/0/attributes/notification_type is related_object_updated
