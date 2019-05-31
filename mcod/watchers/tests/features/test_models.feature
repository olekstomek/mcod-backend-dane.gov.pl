Feature: Testing models from watchers application
  Scenario Outline: Test model-watcher model
    Given I have an instance of <object_name>
    Then I can create a model-watcher from an instance of <object_name>
    And I can't create a model-watcher from given instance of <object_name> again
    And I can't create a model-watcher if an instance of <object_name> is not watchable
    And I can't create a model-watcher if an instance of <object_name> doesn't implement ref_field
    And I can get a model-watcher from an instance of <object_name>
    And I can't get not existing a model-watcher for an instance of <object_name>
    And I can update model-watcher from an instance of <object_name>
    And I can't update model-watcher if an instance of <object_name> hasn't changed
    And I can force updating model-watcher even if an instance of <object_name> hasn't changed
    And I can't update not existing model-watcher from an instance of <object_name>
    And I can update model-watcher without sending notifications
    And I can remove model-watcher created from an instance of <object_name>
    Examples:
      | object_name  |
      | article      |
      | application  |
      | dataset      |
      | organization |
      | resource     |

#  Scenario: Test query-watcher model
#    Creating, updating, deleting and fetching query-watcher from given url (query).
#    Given I have an url
#    Then I can create a query-watcher from given url
#    And I can't create a query-watcher from given the same url again
#    And I can get a query-watcher from an url
#    And I can't get not existing query-watcher for an url
#    And I can update query-watcher data for given url
#    And I can't update not existing query-watcher from an url
