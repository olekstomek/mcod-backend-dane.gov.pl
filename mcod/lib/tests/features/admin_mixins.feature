
  Feature: Admin TrashMixin
    Scenario Outline: Objects can be restored from trash
      Given removed <object_type> objects with ids <object_ids>
      And logged admin user
      When admin user runs restore action for selected <object_type> objects with ids <restored_object_ids>
      Then admin's response status code is 200
      And <object_type> objects with ids <restored_object_ids> are restored from trash
      And <object_type> objects with ids <unrestored_object_ids> are still in trash

      Examples:
      | object_type      | object_ids  | restored_object_ids | unrestored_object_ids |
      | course           | 999,998,997 | 999,998             | 997                   |
      | application      | 999,998,997 | 999,998             | 997                   |
      | article          | 999,998,997 | 999,998             | 997                   |
      | institution      | 999,998,997 | 999,998             | 997                   |
      | category factory | 999,998,997 | 999,998             | 997                   |
      | lab_event        | 999,998,997 | 999,998             | 997                   |
      | guide            | 999,998,997 | 999,998             | 997                   |
      | resource         | 999,998,997 | 999,998             | 997                   |
      | dataset          | 999,998,997 | 999,998             | 997                   |
      | datasource       | 999,998,997 | 999,998             | 997                   |
