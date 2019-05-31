Feature: Tabular data API
  Scenario: Test listing
    Given I have buzzfeed resource with tabular data
    When  I search in tabular data rows
    And I use api version 1.4
    And my language is pl
    And I set request parameter page to 1
    And I set request parameter per_page to 25
    And I send request
    Then response format should be valid
    Then all list items should be of type row
    Then items count should be equal to 1000
