@elasticsearch
Feature: Article details

  Scenario: Article creation automatically creates slug from title
    Given article category with id 999
    When admin's request method is POST
    And admin's request posted article data is {"title": "Article automatically created slug test", "category": 999}
    And admin's page /articles/article/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Article automatically created slug test</a>" został pomyślnie dodany.
    And articles.Article with title Article automatically created slug test contains data {"slug": "article-automatically-created-slug-test"}

  Scenario: Article creation with manually passed slug
    Given article category with id 999
    When admin's request method is POST
    And admin's request posted article data is {"title": "Article created with manual slug test", "category": 999, "slug": "manual-name"}
    And admin's page /articles/article/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Article created with manual slug test</a>" został pomyślnie dodany.
    And articles.Article with title Article created with manual slug test contains data {"slug": "manual-name"}

  Scenario: Article creation saves created_by
    Given article category with id 999
    And admin's request logged admin user created with params {"id": 999}
    When admin's request method is POST
    And admin's request posted article data is {"title": "Article creation saves created_by test", "category": 999}
    And admin's page /articles/article/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Article creation saves created_by test</a>" został pomyślnie dodany.
    And articles.Article with title Article creation saves created_by test contains data {"created_by_id": 999}

  Scenario: Updating of article doesnt overrides created_by
    Given article category with id 999
    And admin user with id 998
    And article created with params {"id": 999, "created_by_id": 998}
    And admin's request logged admin user created with params {"id": 999}
    When admin's request method is POST
    And admin's request posted article data is {"title": "Updating of article doesnt overrides created_by test", "category": 999}
    And admin's page /articles/article/999/change/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Updating of article doesnt overrides created_by test</a>" został pomyślnie zmieniony.
    And articles.Article with title Updating of article doesnt overrides created_by test contains data {"created_by_id": 998, "modified_by_id": 999}

  Scenario: Adding tags to article
    Given article category with id 999
    And article with id 999
    And tag created with params {"id": 999, "name": "Tag1", "language": "pl"}
    When admin's request method is POST
    And admin's request posted article data is {"title": "Adding tags to article test", "slug": "slug-name", "category": 999, "tags_pl": [999]}
    And admin's page /articles/article/999/change/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Adding tags to article test</a>" został pomyślnie zmieniony.
    And article with title Adding tags to article test has tag with id 999
