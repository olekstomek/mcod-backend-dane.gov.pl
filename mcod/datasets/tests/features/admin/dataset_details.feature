@elasticsearch
Feature: Dataset details

  Scenario: Imported dataset is not editable
    Given dataset for data {"id": 999} imported from ckan named Test Source with url http://example.com
    When admin's page /datasets/dataset/999/change/ is requested
    Then admin's response page is not editable

  Scenario: Imported dataset's history page is available for admin
    Given dataset for data {"id": 999} imported from ckan named Test Source with url http://example.com
    When admin's page /datasets/dataset/999/history/ is requested
    Then admin's response status code is 200

  Scenario: Imported dataset's history page is available for editor
    Given institution with id 999
    And admin's request logged editor user created with params {"id": 999, "organizations": [999]}
    And dataset for data {"id": 999, "organization_id": 999} imported from ckan named Test Source with url http://example.com
    When admin's page /datasets/dataset/999/history/ is requested
    Then admin's response status code is 200

  Scenario: Dataset resources tab has pagination
    Given dataset with id 999 and 2 resources
    When admin's page /datasets/dataset/999/change/ is requested
    Then admin's response page contains pagination-block

  Scenario: Dataset creation automatically creates slug from title
    Given institution with id 999
    And tag created with params {"id": 999, "name": "Tag1", "language": "pl"}
    When admin's request method is POST
    And admin's request posted dataset data is {"update_notification_recipient_email": "test@example.com", "title": "Dataset automatically created slug test", "notes": "more than 20 characters", "organization": [999], "tags": [999], "tags_pl": [999]}
    And admin's page /datasets/dataset/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Dataset automatically created slug test</a>" został pomyślnie dodany.
    And datasets.Dataset with title Dataset automatically created slug test contains data {"slug": "dataset-automatically-created-slug-test"}

  Scenario: Admin can add tags to dataset
    Given institution with id 999
    And tag created with params {"id": 999, "name": "Tag1", "language": "pl"}
    When admin's request method is POST
    And admin's request posted dataset data is {"update_notification_recipient_email": "test@example.com", "title": "Admin can add tags to dataset test", "notes": "more than 20 characters", "organization": [999], "tags": [999], "tags_pl": [999]}
    And admin's page /datasets/dataset/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Admin can add tags to dataset test</a>" został pomyślnie dodany.
    And datasets.Dataset with title Admin can add tags to dataset test contains data {"tags_list_as_str": "Tag1"}

  Scenario: Editor can add tags to dataset
    Given institution with id 999
    And tag created with params {"id": 999, "name": "Tag1", "language": "pl"}
    And admin's request logged editor user created with params {"id": 999, "organizations": [999]}
    When admin's request method is POST
    And admin's request posted dataset data is {"update_notification_recipient_email": "test@example.com", "title": "Editor can add tags to dataset test", "notes": "more than 20 characters", "organization": [999], "tags": [999], "tags_pl": [999]}
    And admin's page /datasets/dataset/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Editor can add tags to dataset test</a>" został pomyślnie dodany.
    And datasets.Dataset with title Editor can add tags to dataset test contains data {"tags_list_as_str": "Tag1"}

  Scenario: Dataset creation sets created_by to currently logged user
    Given institution with id 999
    And tag created with params {"id": 999, "name": "Tag1", "language": "pl"}
    And admin's request logged editor user created with params {"id": 999, "organizations": [999]}
    When admin's request method is POST
    And admin's request posted dataset data is {"update_notification_recipient_email": "test@example.com", "title": "Dataset created_by set test", "notes": "more than 20 characters", "organization": [999], "tags": [999], "tags_pl": [999]}
    And admin's page /datasets/dataset/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Dataset created_by set test</a>" został pomyślnie dodany.
    And datasets.Dataset with title Dataset created_by set test contains data {"created_by_id": 999}

  Scenario: Dataset creation with related resource at once
    Given institution with id 999
    And admin's request logged admin user created with params {"id": 999}
    And tag created with params {"id": 999, "name": "Tag1", "language": "pl"}
    When admin's request method is POST
    And admin's request posted dataset data is {"update_notification_recipient_email": "test@example.com", "notes": "more than 20 characters", "organization": [999], "tags": [999], "tags_pl": [999], "resources-2-TOTAL_FORMS": "1", "resources-2-0-switcher": "link", "resources-2-0-link": "https://test.pl", "resources-2-0-title": "123", "resources-2-0-description": "<p>more than 20 characters</p>", "resources-2-0-status": "published", "resources-2-0-id": "", "resources-2-0-dataset": ""}
    And admin's page /datasets/dataset/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Test with dataset title</a>" został pomyślnie dodany.
    And resources.Resource with title 123 contains data {"link": "https://test.pl", "created_by_id": 999, "modified_by_id": 999}

  Scenario: Imported dataset is correctly displayed in trash for admin
    Given dataset for data {"id": 999, "is_removed": true} imported from ckan named Test Source with url http://example.com
    When admin's page /datasets/datasettrash/999/change/ is requested
    Then admin's response page is not editable

  Scenario: Removed dataset is correctly displayed in trash for editor
    Given logged editor user
    And dataset created with params {"id": 999, "is_removed": true}
    When admin's page /datasets/datasettrash/999/change/ is requested
    Then admin's response page is not editable

  Scenario Outline: Dataset details page is properly displayed even if pagination param is invalid
    Given dataset with id 999
    And resource created with params {"id": 998, "title": "dataset resources pagination test", "dataset_id": 999}
    When admin's page <page_url> is requested
    Then admin's response page contains dataset resources pagination test
    Examples:
    | page_url                            |
    | /datasets/dataset/999/change/?p=X   |
    | /datasets/dataset/999/change/?p=999 |
    | /datasets/dataset/999/change/?all=  |

  Scenario: Dataset details page contains related resources
    Given logged editor user
    And dataset with id 999
    And resource created with params {"id": 998, "title": "dataset with resources test", "dataset_id": 999}
    When admin's page /datasets/dataset/999/change is requested
    Then admin's response page contains dataset with resources test

  Scenario: Notification mail is updated after dataset edition by editor
    Given institution with id 999
    And tag created with params {"id": 998, "name": "Tag1", "language": "pl"}
    And admin's request logged editor user created with params {"id": 1000, "organizations": [999], "email": "editor@dane.gov.pl"}
    And dataset with id 1001 and institution 999
    When admin's request method is POST
    And admin's request posted dataset data is {"update_notification_recipient_email": "temp@dane.gov.pl", "organization": [999], "tags_pl": [998]}
    And admin's page /datasets/dataset/1001/change/ is requested
    Then datasets.Dataset with id 1001 contains data {"update_notification_recipient_email": "editor@dane.gov.pl"}

  Scenario: Notification mail is not updated after dataset edition by superuser
    Given institution with id 999
    And tag created with params {"id": 998, "name": "Tag1", "language": "pl"}
    And admin's request logged admin user created with params {"id": 1000, "organizations": [999], "email": "superuser@dane.gov.pl"}
    And dataset with id 1001 and institution 999
    When admin's request method is POST
    And admin's request posted dataset data is {"update_notification_recipient_email": "temp@dane.gov.pl", "organization": [999], "tags_pl": [998]}
    And admin's page /datasets/dataset/1001/change/ is requested
    Then datasets.Dataset with id 1001 contains data {"update_notification_recipient_email": "temp@dane.gov.pl"}

  Scenario: Resource title on inline list redirects to resource admin edit page
    Given dataset with id 999
    And resource created with params {"id": 998, "title": "Title as link", "dataset_id": 999}
    When admin's page /datasets/dataset/999/change/#resources is requested
    Then admin's response page contains <a href="/resources/resource/998/change/">Title as link</a>
