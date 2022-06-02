Feature: ShowcaseProposal details admin
  Scenario: ShowcaseProposal details
    Given dataset with id 999
    And showcaseproposal created with params {"id": 999, "title": "Test showcaseproposal details", "datasets": [999], "category": "app", "applicant_email": "user@example.com"}
    When admin's page /showcases/showcaseproposal/999/change/ is requested
    Then admin's response status code is 200
    And admin's response page contains Test showcaseproposal details
  Scenario: ShowcaseProposal trash
    Given dataset with id 999
    And showcaseproposal created with params {"id": 999, "title": "Test showcaseproposal trash", "datasets": [999], "category": "app", "is_removed": true}
    When admin's page /showcases/showcaseproposaltrash/999/change/ is requested
    Then admin's response status code is 200
    And admin's response page contains Test showcaseproposal trash
  Scenario: ShowcaseProposal acceptation
    Given dataset with id 999
    And showcaseproposal created with params {"id": 999, "title": "Test showcaseproposal acceptation", "datasets": [999], "category": "app", "showcase": null, "keywords": ["tag1"]}
    When admin's request method is POST
    And admin's request posted showcaseproposal data is {"decision": "accepted", "comment": "comment..."}
    And admin's page /showcases/showcaseproposal/999/change/ is requested
    Then admin's response status code is 200
    And admin's response page contains Zadanie utworzenia ponownego wykorzystania zostało uruchomione!
  Scenario: ShowcaseProposal acceptation if already accepted
    Given showcase with id 999
    And showcaseproposal created with params {"id": 999, "title": "Test showcaseproposal acceptation", "showcase_id": 999, "category": "app"}
    When admin's request method is POST
    And admin's request posted showcaseproposal data is {"decision": "accepted", "comment": "comment..."}
    And admin's page /showcases/showcaseproposal/999/change/ is requested
    Then admin's response status code is 200
    And admin's response page not contains Zadanie utworzenia ponownego wykorzystania zostało uruchomione!
