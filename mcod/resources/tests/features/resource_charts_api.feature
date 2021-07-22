@elasticsearch
Feature: Resource charts API
  Scenario: Test delete chart returns status 404 if chart does not exists
    Given logged admin user
    When api request method is DELETE
    And api request path is /1.4/resources/charts/888
    And send api request and fetch the response
    Then api's response status code is 404

  Scenario: Test delete chart returns status 401 if user is not logged in
    Given chart of type default with id 999 for resource with id 999
    When api request method is DELETE
    And api request path is /1.4/resources/charts/999
    And send api request and fetch the response
    Then api's response status code is 401
    And api's response body has no field data

  Scenario: Test delete chart returns status 403 if user does not have required permissions
    Given logged editor user
    And chart of type default with id 999 for resource with id 999
    And logged active user
    When api request method is DELETE
    And api request path is /1.4/resources/charts/999
    And send api request and fetch the response
    Then api's response status code is 403
    And api's response body has no field data

  Scenario: Test delete chart returns 403 if chart is not default and user is not creator of chart
    Given logged editor user
    And chart of type custom with id 999 for resource with id 999
    And logged active user
    When api request method is DELETE
    And api request path is /1.4/resources/charts/999
    And send api request and fetch the response
    Then api's response status code is 403
    And api's response body has no field data

  Scenario: Test delete chart works properly if chart exists
    Given logged admin user
    And chart of type default with id 999 for resource with id 999
    When api request method is DELETE
    And api request path is /1.4/resources/charts/999
    And send api request and fetch the response
    Then api's response status code is 204
    And api's response body has no field data

  Scenario: Test that admin cannot delete someones private chart
    Given logged editor user
    And chart of type private with id 999 for resource with id 999
    And logged admin user
    When api request method is DELETE
    And api request path is /1.4/resources/charts/999
    And send api request and fetch the response
    Then api's response status code is 403
    And api's response body field errors/[0]/title is 403 Forbidden

  Scenario: Test that normal user cannot delete someones private chart
    Given logged editor user
    And chart of type private with id 999 for resource with id 999
    And logged active user
    When api request method is DELETE
    And api request path is /1.4/resources/charts/999
    And send api request and fetch the response
    Then api's response status code is 403
    And api's response body field errors/[0]/title is 403 Forbidden

  Scenario: Test that admin can delete his private chart
    Given logged admin user
    And chart of type private with id 999 for resource with id 999
    When api request method is DELETE
    And api request path is /1.4/resources/charts/999
    And send api request and fetch the response
    Then api's response status code is 204
    And api's response body has no field data

  Scenario: Test that normal user can delete his private chart
    Given logged active user
    And chart of type private with id 999 for resource with id 999
    When api request method is DELETE
    And api request path is /1.4/resources/charts/999
    And send api request and fetch the response
    Then api's response status code is 204
    And api's response body has no field data

  Scenario: Test that admin can delete someones default chart
    Given logged editor user
    And chart of type default with id 999 for resource with id 999
    And logged admin user
    When api request method is DELETE
    And api request path is /1.4/resources/charts/999
    And send api request and fetch the response
    Then api's response status code is 204
    And api's response body has no field data

  Scenario: Test that normal user cannot delete someones default chart
    Given logged editor user
    And chart of type default with id 999 for resource with id 999
    And logged active user
    When api request method is DELETE
    And api request path is /1.4/resources/charts/999
    And send api request and fetch the response
    Then api's response status code is 403
    And api's response body field errors/[0]/title is 403 Forbidden

   Scenario: Test authorized editor from organization can delete chart
     Given logged editor user
     And logged user is from organization of resource 999
     And chart of type default with id 999 for resource with id 999
     When api request method is DELETE
     And api request path is /1.4/resources/charts/999
     And send api request and fetch the response
     Then api's response status code is 204
     And api's response body has no field data

  Scenario: Test resource chart details endpoint returns status code 404 if resource is not found
    Given logged admin user
    When api request method is GET
    And api request path is /1.4/resources/999/chart
    And send api request and fetch the response
    Then api's response status code is 404
    And api's response body field errors/[0]/detail is The requested resource could not be found

  Scenario: Test resource chart details endpoint returns empty data if chart is not found
    Given logged admin user
    And resource with id 999
    When api request method is GET
    And api request path is /1.4/resources/999/chart
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body has field data
    And api's response body field data is None

  Scenario: Test resource chart details endpoint returns empty data if chart for resource exists but is set as removed
    Given logged admin user
    And removed chart of type default with id 999 for resource with id 999
    When api request method is GET
    And api request path is /1.4/resources/999/chart
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body has field data
    And api's response body field data is None

  Scenario: Test anonymous user gets empty data if there is no default chart
    Given resource with id 999
    When api request method is GET
    And api request path is /1.4/resources/999/chart
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field data is None

  Scenario: Test resource chart data endpoint works properly for anonymous user
    Given chart of type default with id 1000 for resource with id 999
    When api request method is GET
    And api request path is /1.4/resources/999/chart
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/type is chart
    And api's response body field /data/id contains 1000

  Scenario: Test resource chart data endpoint works properly for editor
    Given logged editor user
    And chart of type default with id 1000 for resource with id 999
    When api request method is GET
    And api request path is /1.4/resources/999/chart
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/type is chart
    And api's response body field /data/id is 1000

  Scenario: Test create resource chart endpoint is not available for anonymous user
    Given resource with id 888
    When api request method is POST
    And api request path is /1.4/resources/999/chart
    And api request param resource_id is 999
    And send api request and fetch the response
    Then api's response status code is 401
    And api's response body has no field data

  Scenario: Test create resource chart endpoint is available for logged in user
    Given logged active user
    And chart of type default with id 999 for resource with id 999
    When api request method is POST
    And api request path is /1.4/resources/999/chart
    And posted custom chart data is {"x": "col1", "y": "col2"}
    And send api request and fetch the response
    Then api's response status code is 201
    And api's response body has field data

  Scenario: Test update resource chart endpoint is available for logged in user
    Given logged active user
    And chart of type default with id 999 for resource with id 999
    When api request method is POST
    And api request path is /1.4/resources/999/chart
    And posted custom chart data is {"x": "col1", "y": "col2"}
    And send api request and fetch the response
    Then api's response status code is 201
    And api's response body field data/id is not 999

  Scenario: Test update default resource chart endpoint is not available for normal user
    Given logged editor user
    And chart of type default with id 999 for resource with id 999
    And logged active user
    When api request method is POST
    And api request language is pl
    And api request path is /1.4/resources/999/chart
    And posted default chart data is {"x": "col1", "y": "col2"}
    And send api request and fetch the response
    Then api's response status code is 403
    And api's response body field errors/[0]/title is Brak uprawnień do definiowania wykresu

  Scenario: Test update resource chart endpoint returns error if chart data is empty
    Given logged active user
    And chart of type default with id 999 for resource with id 999
    When api request method is POST
    And api request path is /1.4/resources/999/chart
    And posted custom chart data is None
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field errors/[0]/source/pointer is /data/attributes/chart

  Scenario: Test update resource chart endpoint updates default chart instead of creation of another
    Given logged admin user
    And chart of type default with id 999 for resource with id 999
    When api request method is POST
    And api request path is /1.4/resources/999/chart
    And posted default chart data is {"x": "col1", "y": "col2"}
    And send api request and fetch the response
    Then api's response status code is 201
    And api's response body field data/attributes/is_default is True
    And api's response body field data/id is 999

  Scenario: Test editor cannot create chart for resource not related to his organization
    Given logged editor user
    And logged user is from organization of resource 1000
    And resource with id 1001
    When api request method is POST
    And api request language is pl
    And api request path is /1.4/resources/1001/chart
    And posted default chart data is {"x": "col1", "y": "col2"}
    And send api request and fetch the response
    Then api's response status code is 403
    And api's response body field errors/[0]/title is Brak uprawnień do definiowania wykresu

  Scenario: Test editor can create chart for resource related to his organization
    Given logged editor user
    And logged user is from organization of resource 1000
    When api request method is POST
    And api request language is pl
    And api request path is /1.4/resources/1000/chart
    And posted default chart data is {"x": "col1", "y": "col2"}
    And send api request and fetch the response
    Then api's response status code is 201
    And api's response body field data/attributes/is_default is True
    And api's response body field data/attributes/chart/x is col1
    And api's response body field data/attributes/chart/y is col2

  Scenario: Test resource charts endpoint returns empty list if there is no charts for specified resource
    Given logged editor user
    And resource with id 999
    When api request method is GET
    And api request path is /1.4/resources/999/charts
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field data is []

  Scenario: Test resource charts endpoint returns default chart only if user is not authenticated
    Given two charts for resource with id 999
    When api request method is GET
    And api request path is /1.4/resources/999/charts
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field data/[0]/attributes/is_default is True
    And size of api's response body field data is 1

  Scenario: Test resource charts endpoint returns default and custom charts if the custom is created by the user
    Given logged editor user
    And two charts for resource with id 999
    When api request method is GET
    And api request path is /1.4/resources/999/charts
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field data/[0]/attributes/is_default is True
    And api's response body field data/[1]/attributes/is_default is False
    And size of api's response body field data is 2
