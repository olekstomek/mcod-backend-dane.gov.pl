  Feature: Model instances removal
    Scenario Outline: Remove model instances
      Given factory <object_type> with params <params>
      When admin's request method is GET
      And changelist for <object_type> is requested
      Then admin's response status code is 200
      And <object_type> has trash if <has_trash>
      And object is deletable in admin panel if <can_delete>
      And object can be removed from database by button if <can_delete> and <can_remove_from_db>
      And object can be removed from database by action if <can_delete> and <can_remove_from_db>
      And object can be removed from database by model delete method if <can_delete> and <can_remove_from_db>
      And object can be removed from database by queryset delete method if <can_delete> and <can_remove_from_db>

    Examples:
    | object_type               |                              params| has_trash | can_delete | can_remove_from_db |
    | course                    |                       {"id": 1001} |         1 |          1 |                  0 |
#    | application               |                       {"id": 1001} |         1 |          1 |                  0 |
#    | applicationproposal       |                       {"id": 1001} |         1 |          1 |                  0 |
    | article                   |                       {"id": 1001} |         1 |          1 |                  0 |
    | search history            |                       {"id": 1001} |         0 |          1 |                  1 |
    | institution               |                       {"id": 1001} |         1 |          1 |                  0 |
    | category                  |                       {"id": 1001} |         1 |          1 |                  0 |
    | lab_event                 |                       {"id": 1001} |         1 |          1 |                  0 |
    | newsletter                |                       {"id": 1001} |         0 |          1 |                  1 |
    | submission                |                       {"id": 1001} |         0 |          0 |                  0 |
    | subscription              |                       {"id": 1001} |         0 |          1 |                  1 |
    | guide                     |                       {"id": 1001} |         1 |          1 |                  0 |
    | organizationreport        |                       {"id": 1001} |         0 |          1 |                  1 |
    | userreport                |                       {"id": 1001} |         0 |          1 |                  1 |
    | resourcereport            |                       {"id": 1001} |         0 |          1 |                  1 |
    | datasetreport             |                       {"id": 1001} |         0 |          1 |                  1 |
    | summarydailyreport        |                       {"id": 1001} |         0 |          1 |                  1 |
    | monitoringreport          |                       {"id": 1001} |         0 |          1 |                  1 |
    | tag                       |     {"id": 1001, "language": "pl"} |         0 |          1 |                  1 |
    | meeting                   |                       {"id": 1001} |         1 |          1 |                  0 |
    | active user               |                       {"id": 1001} |         0 |          1 |                  0 |
    | resource                  |                       {"id": 1001} |         1 |          1 |                  0 |
    | dataset                   |                       {"id": 1001} |         1 |          1 |                  0 |
    | datasetsubmission         |                       {"id": 1001} |         1 |          1 |                  0 |
    | resourcecomment           |                       {"id": 1001} |         1 |          1 |                  0 |
    | datasetcomment            |                       {"id": 1001} |         1 |          1 |                  0 |
    | accepteddatasetsubmission |                       {"id": 1001} |         1 |          1 |                  0 |
    | specialsign               |                       {"id": 1001} |         0 |          1 |                  0 |
    | datasourceimport          |                       {"id": 1001} |         0 |          0 |                  0 |
    | datasource                | {"id": 1001, "status": "inactive"} |         1 |          1 |                  0 |
    | datasource                |   {"id": 1002, "status": "active"} |         1 |          0 |                  0 |
    | showcase                  |                       {"id": 1001} |         1 |          1 |                  0 |
    | showcaseproposal          |                       {"id": 1001} |         1 |          1 |                  0 |


    Scenario Outline: Remove model instances from trash
      Given removed factory <object_type> with params <params>
      When admin's request method is GET
      And trash changelist for <object_type> is requested
      Then admin's response status code is 200
      And removed object is flagged as permanently removed after deleted from trash by button
      And removed object is flagged as permanently removed after deleted from trash by action
      And removed object is flagged as permanently removed after deleted from trash by model delete method
      And removed object is flagged as permanently removed after deleted from trash by trash queryset delete method

    Examples:
    | object_type               |                             params |
    | course                    |                       {"id": 1003} |
#    | application               |                       {"id": 1003} |
#    | applicationproposal       |                       {"id": 1003} |
    | article                   |                       {"id": 1003} |
    | institution               |                       {"id": 1003} |
    | category                  |                       {"id": 1003} |
    | lab_event                 |                       {"id": 1003} |
    | guide                     |                       {"id": 1003} |
    | meeting                   |                       {"id": 1003} |
    | resource                  |                       {"id": 1003} |
    | dataset                   |                       {"id": 1003} |
    | datasetsubmission         |                       {"id": 1003} |
    | resourcecomment           |                       {"id": 1003} |
    | datasetcomment            |                       {"id": 1003} |
    | accepteddatasetsubmission |                       {"id": 1003} |
    | datasource                | {"id": 1003, "status": "inactive"} |
    | showcase                  |                       {"id": 1003} |
    | showcaseproposal          |                       {"id": 1003} |
