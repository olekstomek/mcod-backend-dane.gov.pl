@elasticsearch
Feature: Subscriptions API

  Scenario: Listing for logged user in API 1.4
    Given logged active user
    And subscription with id 999 of article with id 999 as article-1
    And second subscription with id 998 of dataset with id 999 as dataset-1
    And subscription with id 997 of removed article with id 888 as removed-article-1
    And subscription with id 995 of draft article with id 777 as draft-article-1
    And admin has subscription with id 888 of article with id 222 as article-admin-1
    And admin has second subscription with id 666 of dataset with id 224 as dataset-admin-1
    When api request method is GET
    And api request path is /auth/subscriptions
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body field /data/*/type is subscription
    And api's response body has field /data/*/attributes/name
    And api's response body has field /data/*/attributes/created
    And api's response body has field /data/*/attributes/modified
    And api's response body has field /data/*/attributes/customfields
    And api's response body has field /data/*/relationships/subscribed_object
    And api's response body field /data/[0]/attributes/name is dataset-1
    And api's response body field /data/[1]/attributes/name is article-1
    And api's response body field /data/[0]/relationships/subscribed_object/data/type is dataset
    And api's response body field /data/[1]/relationships/subscribed_object/data/type is article
    And api's response body field /data/*/attributes/name is not article-admin-1
    And api's response body field /data/*/attributes/name is not dataset-admin-1
    And api's response body field /data/*/attributes/name is not removed-article-1
    And api's response body field /data/*/attributes/name is not draft-article-1

  Scenario: Listing for anonymous user in API 1.4
    Given admin has subscription with id 888 of article with id 222 as article-admin-1
    And admin has second subscription with id 666 of dataset with id 224 as dataset-admin-1
    When api request method is GET
    And api request path is /auth/subscriptions
    And send api request and fetch the response
    Then api's response status code is 401
    And size of api's response body field /errors is 1
    And api's response body field /errors/[0]/code is 401_unauthorized

  Scenario Outline: Listing filtering for logged user in API 1.4
    Given logged active user
    And subscription with id 999 of resource with id 1111 as res-1111
    And second subscription with id 998 of institution with id 333 as inst-333
    And third subscription with id 988 of institution with id 444 as 545454334
    And 3 subscriptions of random article
    And and 4 subscriptions of random application
    And also 5 subscriptions of random dataset
    And query subscription with id 555 for url http://api.test.mcod/datasets as two_datasets
    When api request method is GET
    And api request path is /auth/subscriptions
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 16
    And api's response body field /data/*/attributes/name contains two_datasets
    And api request path is <request_path>
    And send api request and fetch the response
    And api's response body field <resp_body_field> is <resp_body_value>
    And api's response body has field /data/*/relationships/subscribed_object
    Examples:
      | request_path                                | resp_body_value | resp_body_field |
      | /auth/subscriptions?object_name=article     | 3               | /meta/count     |
      | /auth/subscriptions?object_name=application | 4               | /meta/count     |
      | /auth/subscriptions?object_name=dataset     | 5               | /meta/count     |
      | /auth/subscriptions?object_name=institution | 2               | /meta/count     |
      | /auth/subscriptions?object_name=resource    | 1               | /meta/count     |
      | /auth/subscriptions?object_name=query       | 1               | /meta/count     |

  Scenario: Listing filtering with invalid id for logged user in API 1.4
    Given logged active user
    And subscription with id 998 of institution with id 333 as inst-333
    And second subscription with id 988 of article with id 444 as 545454334
    When api request method is GET
    And api request path is /auth/subscriptions?object_name=invalid_object
    And send api request and fetch the response
    Then api's response status code is 422

  Scenario Outline: Listing filtering with object name and object_id for logged user in API 1.4
    Given logged active user
    And subscription with id 999 of institution with id 1111 as inst-1111
    And second subscription with id 998 of article with id 333 as art-333
    And third subscription with id 988 of application with id 444 as app-444
    And 3 subscriptions of random article
    And and 4 subscriptions of random application
    And query subscription with id 555 for url http://api.test.mcod/datasets as two_datasets
    When api request method is GET
    And api request path is /auth/subscriptions
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 11
    And api request path is <request_path>
    And send api request and fetch the response
    And api's response body field /meta/count is 1
    And api's response body has field /data/*/relationships/subscribed_object
    And api's response body field <resp_body_field> is <resp_body_value>
    Examples:
      | request_path                                               | resp_body_value | resp_body_field                                   |
      | /auth/subscriptions?object_name=institution&object_id=1111 | institution     | /data/*/relationships/subscribed_object/data/type |
      | /auth/subscriptions?object_name=article&object_id=333      | article         | /data/*/relationships/subscribed_object/data/type |
      | /auth/subscriptions?object_name=application&object_id=444  | application     | /data/*/relationships/subscribed_object/data/type |

  Scenario: Listing filtering without object name and with object_id for logged user in API 1.4
    Given logged active user
    And subscription with id 999 of institution with id 1111 as inst-1111
    And second subscription with id 998 of article with id 1111 as art-1111
    And third subscription with id 997 of application with id 222 as app-1111
    When api request method is GET
    And api request path is /auth/subscriptions?object_id=1111
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body field /data/[0]/attributes/name is art-1111
    And api's response body field /data/[1]/attributes/name is inst-1111
    And api's response body field /data/[0]/relationships/subscribed_object/data/type is article
    And api's response body field /data/[1]/relationships/subscribed_object/data/type is institution

  Scenario: Listing filtering with invalid object_id for logged user in API 1.4
    Given logged active user
    And subscription with id 999 of institution with id 1111 as inst-1111
    When api request method is GET
    And api request path is /auth/subscriptions?object_id=1112
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 0
    And api request path is /auth/subscriptions?object_name=institution&object_id=1113
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 0

  Scenario: Subscription with id 999 in API 1.4
    Given logged active user
    And subscription with id 999 of article with id 999 as article-1
    When api request method is GET
    And api request path is /auth/subscriptions/999
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/type is subscription
    And api's response body field /data/id is 999
    And api's response body field /data/attributes/name is article-1
    And api's response body has field /data/attributes/created
    And api's response body has field /data/attributes/modified
    And api's response body has field /data/attributes/customfields
    And api's response body has field /data/relationships/subscribed_object
    And size of api's response body field /included is 1
    And api's response body field /data/relationships/subscribed_object/data/type is article

  Scenario Outline: Object subscription in API 1.4
    Given logged active user
    And <object_type> with id 900
    When api request method is POST
    And api request path is /auth/subscriptions
    And api request body field /data/type is subscription
    And api request body field <req_body_field> is <req_body_value>
    And api request body field /data/attributes/object_ident is 900
    And api request body field /data/attributes/name is my-subscription
    And api request body field /data/attributes/customfields/something is nothing
    And send api request and fetch the response
    Then api's response status code is 201
    And api's response body field /data/attributes/name is my-subscription
    And api's response body field /data/relationships/subscribed_object/data/id is 900
    And api's response body field /data/attributes/customfields/something is nothing
    And api's response body field /data/type is subscription
    And api's response body has field /data/attributes/created
    And api's response body has field /data/attributes/modified
    And api's response body has field /data/attributes/customfields
    And api request method is GET
    And api request path is /auth/subscriptions
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/[0]/relationships/subscribed_object/data/id is 900
    And api's response body field /data/[0]/attributes/customfields/something is nothing
    And api's response body field /data/[0]/attributes/name is my-subscription
    And size of api's response body field /included is 1
    And api's response body field /data/[0]/type is subscription
    And api's response body has field /data/[0]/attributes/created
    And api's response body has field /data/[0]/attributes/modified
    And api's response body has field /data/[0]/attributes/customfields

    Examples:
      | object_type | req_body_field               | req_body_value |
      | dataset     | /data/attributes/object_name | dataset        |
      | article     | /data/attributes/object_name | article        |
      | application | /data/attributes/object_name | application    |
      | institution | /data/attributes/object_name | institution    |
      | resource    | /data/attributes/object_name | resource       |

  Scenario Outline: Subscribe object as not logged user in API 1.4
    Given <object_type> with id 900
    When api request method is POST
    And api request path is /auth/subscriptions
    And api request body field /data/type is subscription
    And api request body field <req_body_field> is <req_body_value>
    And api request body field /data/attributes/object_ident is 900
    And api request body field /data/attributes/customfields/something is nothing
    And send api request and fetch the response
    Then api's response status code is 401

    Examples:
      | object_type | req_body_value | req_body_field               |
      | dataset     | dataset        | /data/attributes/object_name |
      | article     | article        | /data/attributes/object_name |
      | application | application    | /data/attributes/object_name |
      | institution | institution    | /data/attributes/object_name |
      | resource    | resource       | /data/attributes/object_name |

  Scenario: Subscription with id 999 for anonymous user in API 1.4
    Given admin has subscription with id 999 of article with id 999 as article-admin-1
    And admin has second subscription with id 998 of dataset with id 999 as dataset-admin-1
    When api request method is GET
    And api request path is /auth/subscriptions/999
    And send api request and fetch the response
    Then api's response status code is 401
    And api's response body field /errors/[0]/code is 401_unauthorized

  Scenario: Admin's subscription with id not accessable for other user in API 1.4
    Given logged active user
    And admin has subscription with id 999 of article with id 999 as article-admin-1
    When api request method is GET
    And api request path is /auth/subscriptions/999
    And send api request and fetch the response
    Then api's response status code is 404
    And api's response body field /errors/[0]/code is 404_not_found

  Scenario: Change subscription for article in API 1.4
    Given logged active user
    And subscription with id 999 of article with id 888 as article-1
    When api request method is PATCH
    And api request path is /auth/subscriptions/999
    And api request body field /data/type is subscription
    And api request body field /data/id is 999
    And api request body field /data/attributes/name is my-subscription
    And api request body field /data/attributes/customfields/something is nothing
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/attributes/name is my-subscription
    And api's response body field /data/attributes/customfields/something is nothing
    And size of api's response body field /included is 1
    And api's response body field /included/[0]/type is article
    And api request path is /auth/subscriptions/
    And api request method is GET
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/[0]/attributes/name is my-subscription
    And api's response body field /data/[0]/attributes/customfields/something is nothing
    And size of api's response body field /included is 1
    And api's response body field /included/[0]/type is article

  Scenario: Delete subscription for dataset in API 1.4
    Given logged active user
    And subscription with id 999 of dataset with id 1000 as dataset-1
    And second subscription with id 998 of dataset with id 999 as dataset-2
    When api request method is DELETE
    And api request path is /auth/subscriptions/999
    And send api request and fetch the response
    Then api's response status code is 204
    And api request method is GET
    And send api request and fetch the response
    And api's response status code is 404
    And api request path is /auth/subscriptions
    And send api request and fetch the response
    And api's response body field /meta/count is 1
    And api's response body field /data/[0]/attributes/name is dataset-2

  Scenario: User can create only one subscription of an application
    Given logged active user
    And subscription with id 999 of article with id 999 as article-1
    When api request method is POST
    And api request path is /auth/subscriptions
    And api request body field /data/type is subscription
    And api request body field /data/attributes/object_name is article
    And api request body field /data/attributes/object_ident is 999
    And api request body field /data/attributes/name is new-name
    And api request body field /data/attributes/customfields/something is nothing
    And send api request and fetch the response
    Then api's response status code is 403
    And api request method is GET
    And api request path is /auth/subscriptions
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/[0]/attributes/name is article-1
    And api's response body field /data/[0]/attributes/customfields is None

  Scenario Outline: Subscription info available on objects listing for logged user in api 1.4
    Given logged active user
    And admin has subscription with id 900 of <object_type> with id 900 as admin-subscription-900
    And admin has subscription with id 901 of <object_type> with id 901 as admin-subscription-901
    And subscription with id 999 of <object_type> with id 999 as subscription-999
    And subscription with id 998 of <object_type> with id 998 as subscription-998
    And subscription with id 997 of <object_type> with id 997 as subscription-997
    And <object_type> with id 903
    And <object_type> with id 904
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 7
    And api's response body has no field /data/[0]/relationships/subscription
    And api's response body has no field /data/[1]/relationships/subscription
    And api's response body has no field /data/[5]/relationships/subscription
    And api's response body has no field /data/[6]/relationships/subscription
    And api's response body field /data/[2]/relationships/subscription/data/type is subscription
    And api's response body field /data/[3]/relationships/subscription/data/type is subscription
    And api's response body field /data/[4]/relationships/subscription/data/type is subscription

    Examples:
      | object_type | request_path      |
      | article     | /1.4/articles     |
      | application | /1.4/applications |
      | institution | /1.4/institutions |
      | dataset     | /1.4/datasets     |
      | resource    | /1.4/resources    |

  Scenario Outline: Subscription info available on objects listing for logged user in api 1.0
    Given logged active user
    And admin has subscription with id 900 of <object_type> with id 900 as admin-subscription-900
    And admin has subscription with id 901 of <object_type> with id 901 as admin-subscription-901
    And subscription with id 999 of <object_type> with id 999 as subscription-999
    And subscription with id 998 of <object_type> with id 998 as subscription-998
    And subscription with id 997 of <object_type> with id 997 as subscription-997
    And <object_type> with id 903
    And <object_type> with id 904
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 7
    And api's response body has no field /data/[0]/relationships/subscription
    And api's response body has no field /data/[1]/relationships/subscription
    And api's response body has no field /data/[5]/relationships/subscription
    And api's response body has no field /data/[6]/relationships/subscription
    And api's response body has field /data/[2]/relationships/subscription
    And api's response body has field /data/[3]/relationships/subscription
    And api's response body has field /data/[4]/relationships/subscription
    Examples:
      | object_type | request_path      |
      | article     | /1.0/articles     |
      | application | /1.0/applications |
      | institution | /1.0/institutions |
      | dataset     | /1.0/datasets     |
      | resource    | /1.0/resources    |

  Scenario Outline: Subscription info available in object with id 999 for logged user in api 1.4
    Given logged active user
    And subscription with id 999 of <object_type> with id 999 as subscription-999
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/[0]/relationships/subscription/data/type is subscription
    And api's response body field /data/[0]/relationships/subscription/data/id is 999

    Examples:
      | object_type | request_path      |
      | article     | /1.4/articles     |
      | application | /1.4/applications |
      | institution | /1.4/institutions |
      | dataset     | /1.4/datasets     |
      | resource    | /1.4/resources    |

  Scenario Outline: Subscription info available in object with id 999 for logged user in api 1.0
    Given logged active user
    And subscription with id 999 of <object_type> with id 999 as subscription-999
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body has field /data/[0]/relationships/subscription

    Examples:
      | object_type | request_path      |
      | article     | /1.0/articles     |
      | application | /1.0/applications |
      | institution | /1.0/institutions |
      | dataset     | /1.0/datasets     |
      | resource    | /1.0/resources    |

  Scenario Outline: Subscription info not available in object with id 999 for logged user in api 1.4 and 1.0
    Given logged active user
    And admin has subscription with id 900 of <object_type> with id 900 as admin-subscription-900
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body has no field /data/[0]/relationships/subscription


    Examples:
      | object_type | request_path      |
      | article     | /1.4/articles     |
      | application | /1.4/applications |
      | institution | /1.4/institutions |
      | dataset     | /1.4/datasets     |
      | resource    | /1.4/resources    |
      | article     | /1.0/articles     |
      | application | /1.0/applications |
      | institution | /1.0/institutions |
      | dataset     | /1.0/datasets     |
      | resource    | /1.0/resources    |

  Scenario Outline: Subscription info not available in object with id 999 for anonymous user in api 1.4 and 1.0
    Given admin has subscription with id 900 of <object_type> with id 900 as admin-subscription-900
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body has no field /data/[0]/relationships/subscription

    Examples:
      | object_type | request_path      |
      | article     | /1.4/articles     |
      | application | /1.4/applications |
      | institution | /1.4/institutions |
      | dataset     | /1.4/datasets     |
      | resource    | /1.4/resources    |
      | article     | /1.0/articles     |
      | application | /1.0/applications |
      | institution | /1.0/institutions |
      | dataset     | /1.0/datasets     |
      | resource    | /1.0/resources    |


  Scenario Outline: Deleted subscription is not available on article listing in api 1.4 and 1.0
    Given logged active user
    And subscription with id 999 of <object_type> with id 999 as subscription-999
    And subscription with id 998 of <object_type> with id 998 as subscription-998
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body has field /data/*/relationships/subscription
    And api request method is DELETE
    And api request path is /auth/subscriptions/999
    And send api request and fetch the response
    And api's response status code is 204
    And api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response status code is 200
    And api's response body has field /data/0/relationships/subscription
    And api's response body has no field /data/1/relationships/subscription

    Examples:
      | object_type | request_path      |
      | article     | /1.4/articles     |
      | application | /1.4/applications |
      | institution | /1.4/institutions |
      | dataset     | /1.4/datasets     |
      | resource    | /1.4/resources    |
      | article     | /1.0/articles     |
      | application | /1.0/applications |
      | institution | /1.0/institutions |
      | dataset     | /1.0/datasets     |
      | resource    | /1.0/resources    |

  Scenario Outline: Deleted subscription is not available on object listing in api 1.4 and 1.0
    Given logged active user
    And subscription with id 999 of <object_type> with id 999 as subscription-999
    And subscription with id 998 of <object_type> with id 998 as subscription-998
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body has field /data/*/relationships/subscription
    And api request method is DELETE
    And api request path is /auth/subscriptions/999
    And send api request and fetch the response
    And api's response status code is 204
    And api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response status code is 200
    And api's response body has field /data/[0]/relationships/subscription
    And api's response body has no field /data/[1]/relationships/subscription
    And api request method is GET

  Examples:
      | object_type | request_path      |
      | article     | /1.4/articles     |
      | application | /1.4/applications |
      | institution | /1.4/institutions |
      | dataset     | /1.4/datasets     |
      | resource    | /1.4/resources    |
      | article     | /1.0/articles     |
      | application | /1.0/applications |
      | institution | /1.0/institutions |
      | dataset     | /1.0/datasets     |
      | resource    | /1.0/resources    |

  Scenario: Subscribe query as logged user in API 1.4
    Given logged active user
    When api request method is POST
    And api request path is /auth/subscriptions
    And api request body field /data/type is subscription
    And api request body field /data/attributes/object_name is query
    And api request body field /data/attributes/object_ident is http://api.test.mcod/datasets
    And api request body field /data/attributes/customfields/something is nothing
    And send api request and fetch the response
    Then api's response status code is 201
    And api's response body field /data/attributes/name is query-http://api.test.mcod/datasets
    And api's response body field /data/relationships/subscribed_object/data/type is query
    And api's response body field /data/relationships/subscribed_object/data/id is http://api.test.mcod/datasets
    And api's response body field /data/type is subscription
    And api's response body field /data/attributes/customfields/something is nothing
    And api's response body has field /data/attributes/created
    And api's response body has field /data/attributes/modified
    And api's response body has field /data/attributes/customfields
    And api request method is GET
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/[0]/attributes/name is query-http://api.test.mcod/datasets
    And api's response body field /data/[0]/relationships/subscribed_object/data/type is query
    And api's response body field /data/[0]/relationships/subscribed_object/data/id is http://api.test.mcod/datasets
    And api's response body field /data/*/type is subscription
    And api's response body field /data/[0]/attributes/customfields/something is nothing
    And api's response body has field /data/*/attributes/created
    And api's response body has field /data/*/attributes/modified
    And api's response body has field /data/*/attributes/customfields

  Scenario: Subscribe query with wrong url as logged user in API 1.4
    Given logged active user
    When api request method is POST
    And api request path is /auth/subscriptions
    And api request body field /data/type is subscription
    And api request body field /data/attributes/object_name is query
    And api request body field /data/attributes/object_ident is https://www.google.com/search?q=dane
    And api request body field /data/attributes/customfields/something is nothing
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field /errors/[0]/code is 422_unprocessable_entity
    And size of api's response body field errors is 1

  Scenario: Subscribe query with wrong url as anonymous user in API 1.4
    When api request method is POST
    And api request path is /auth/subscriptions
    And api request body field /data/type is subscription
    And api request body field /data/attributes/object_name is query
    And api request body field /data/attributes/object_ident is http://api.test.mcod/datasets
    And api request body field /data/attributes/customfields/something is nothing
    And send api request and fetch the response
    Then api's response status code is 401
    And api's response body field /errors/[0]/code is 401_unauthorized
    And size of api's response body field errors is 1

  Scenario: Subscribe invalid object as logged user in API 1.4
    Given logged active user
    When api request method is POST
    And api request path is /auth/subscriptions
    And api request body field /data/type is subscription
    And api request body field /data/attributes/object_name is invalid_object
    And api request body field /data/attributes/object_ident is 123
    And api request body field /data/attributes/customfields/something is nothing
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field /errors/[0]/code is 422_unprocessable_entity
    And size of api's response body field errors is 1

  Scenario: Subscribe query twice as logged user in API 1.4
    Given logged active user
    And query subscription with id 999 for url http://api.test.mcod/datasets?a=1&b=2&c=3 as first-query
    When api request method is POST
    And api request path is /auth/subscriptions
    And api request body field /data/type is subscription
    And api request body field /data/attributes/object_name is query
    And api request body field /data/attributes/object_ident is http://api.test.mcod/datasets?b=2&c=3&a=1
    And api request body field /data/attributes/customfields/something is nothing
    And send api request and fetch the response
    Then api's response status code is 403
    And api's response body field /errors/[0]/code is 403_forbidden
    And size of api's response body field errors is 1

  Scenario: Subscription with duplicated name as logged user in API 1.4
    Given logged active user
    And query subscription with id 999 for url http://api.test.mcod/datasets?c=123 as test-query
    When api request method is POST
    And api request path is /auth/subscriptions
    And api request body field /data/type is subscription
    And api request body field /data/attributes/object_name is query
    And api request body field /data/attributes/name is test-query-1
    And api request body field /data/attributes/object_ident is http://api.test.mcod/datasets?a=123
    And send api request and fetch the response
    Then api's response status code is 201
    And api request path is /auth/subscriptions
    And api request body field /data/type is subscription
    And api request body field /data/attributes/object_name is query
    And api request body field /data/attributes/name is test-query
    And api request body field /data/attributes/object_ident is http://api.test.mcod/datasets?d=123
    And send api request and fetch the response
    And api's response status code is 403
    And api's response body field /errors/[0]/code is 403_forbidden
    And size of api's response body field errors is 1
    And api request method is PATCH
    And api request body field /data is of type dict
    And api request path is /auth/subscriptions/999
    And api request body field /data/type is subscription
    And api request body field /data/id is 999
    And api request body field /data/attributes/name is test-query-1
    And send api request and fetch the response
    And api's response status code is 403
    And api's response body field /errors/[0]/code is 403_forbidden
    And size of api's response body field errors is 1

  Scenario: Update query subscription as logged user in API 1.4
    Given logged active user
    And query subscription with id 999 for url http://api.test.mcod/datasets?a=1&b=2&c=3 as first-query
    And subscription with id 997 of article with id 997 as subscription-997
    When api request method is PATCH
    And api request path is /auth/subscriptions/999
    And api request body field /data/type is subscription
    And api request body field /data/id is 999
    And api request body field /data/attributes/name is changed-name
    And api request body field /data/attributes/customfields/something is nothing
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/attributes/name is changed-name
    And api's response body field /data/attributes/customfields/something is nothing
    And api request method is GET
    And api request path is /auth/subscriptions
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body field /data/[1]/attributes/name is changed-name
    And api's response body field /data/[1]/relationships/subscribed_object/data/type is query
    And api's response body field /data/[1]/relationships/subscribed_object/data/id is http://api.test.mcod/datasets?a=1&b=2&c=3
    And api's response body field /data/[1]/attributes/customfields/something is nothing
    And api's response body field /data/*/type is subscription
    And api's response body has field /data/*/attributes/created
    And api's response body has field /data/*/attributes/modified
    And api's response body has field /data/*/attributes/customfields

  Scenario: Delete query subscription as logged user in API 1.4
    Given logged active user
    And query subscription with id 999 for url http://api.test.mcod/datasets?a=1&b=2&c=3 as first-query
    And subscription with id 998 of article with id 998 as subscription-998
    When api request method is DELETE
    And api request path is /auth/subscriptions/999
    And send api request and fetch the response
    Then api's response status code is 204
    And api request method is GET
    And send api request and fetch the response
    And api's response status code is 404
    And api request path is /auth/subscriptions
    And send api request and fetch the response
    And api's response body field /meta/count is 1
    And api's response body field /data/[0]/attributes/name is subscription-998

  Scenario: Subscribed query flag as logged user in API 1.4
    Given logged active user
    And dataset with id 900
    And dataset with id 901
    And article with id 902
    And article with id 903
    And query subscription with id 999 for url http://api.test.mcod/1.4/datasets?c=1&b=2 as datasets-listing
    And admin has query subscription with id 998 for url http://api.test.mcod/1.4/articles as admin-articles
    When api request method is GET
    And api request path is /1.4/datasets?b=2&c=1
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/subscription_url is http://api.test.mcod/auth/subscriptions/999
    And api request method is GET
    And api request path is /1.4/articles
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body has no field subscribed_url


  Scenario: Subscribed query flag as logged user in API 1.0
    Given logged active user
    And dataset with id 900
    And dataset with id 901
    And article with id 902
    And article with id 903
    And query subscription with id 999 for url http://api.test.mcod/1.0/datasets as datasets-listing
    And admin has query subscription with id 998 for url http://api.test.mcod/1.0/articles as admin-articles
    When api request method is GET
    And api request path is /1.0/datasets
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/subscription_url is http://api.test.mcod/auth/subscriptions/999
    And api request method is GET
    And api request path is /1.0/articles
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body has no field subscribed_url

  Scenario: Subscribed query flag as anonymous user in API 1.4
    Given article
    And admin has query subscription with id 999 for url http://api.test.mcod/articles as admin-articles
    When api request method is GET
    And api request path is /articles
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body has no field subscribed_url

  Scenario: Subscribed query flag as anonymous user in API 1.0
    Given article
    And admin has query subscription with id 999 for url http://api.test.mcod/articles as admin-articles
    When api request method is GET
    And api request path is /1.4/articles
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body has no field subscribed_url

  Scenario Outline: Subscribed object has been changed to draft in API 1.4
    Given logged active user
    And subscription with id 999 of <object_type> with id 999 as subscription-999
    And subscription with id 998 of <object_type> with id 998 as subscription-998
    When api request method is GET
    And api request path is /1.4/auth/subscriptions
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body field /data/[0]/attributes/name is subscription-998
    And api request path is /1.4/auth/subscriptions/999
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /data/attributes/name is subscription-999
    And set status draft on <object_type> with id 999
    And api request path is /1.4/auth/subscriptions
    And send api request and fetch the response
    And api's response body field /meta/count is 1
    And api request path is /1.4/auth/subscriptions/999
    And send api request and fetch the response
    And api's response status code is 404
    And set status published on <object_type> with id 999
    And api request path is /1.4/auth/subscriptions
    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api request path is /1.4/auth/subscriptions/999
    And send api request and fetch the response
    And api's response status code is 200

    Examples:
      | object_type |
      | article     |
      | application |
      | dataset     |
      | institution |
      | resource    |

  Scenario Outline: Subscribed object has been removed in API 1.4
    Given logged active user
    And subscription with id 999 of <object_type> with id 999 as subscription-999
    And subscription with id 998 of <object_type> with id 998 as subscription-998
    When api request method is GET
    And api request path is /1.4/auth/subscriptions
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body field /data/[1]/attributes/name is subscription-999
    And api request path is /1.4/auth/subscriptions/999
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /data/attributes/name is subscription-999
    And remove <object_type> with id 999
    And api request path is /1.4/auth/subscriptions
    And send api request and fetch the response
    And api's response body field /meta/count is 1
    And api's response body field /data/[0]/attributes/name is subscription-998
    And api request path is /1.4/auth/subscriptions/999
    And send api request and fetch the response
    And api's response status code is 404
    And api request path is /1.4/auth/subscriptions
    And restore <object_type> with id 999
    And send api request and fetch the response
    And api's response body field /meta/count is 2
    And api's response body field /data/[1]/attributes/name is subscription-999
    And api request path is /1.4/auth/subscriptions/999
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /data/attributes/name is subscription-999

    Examples:
      | object_type |
      | article     |
      | application |
      | dataset     |
      | institution |
      | resource    |
