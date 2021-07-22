@elasticsearch
Feature: Articles' API
  Scenario: Listing in API 1.4
    Given article with id 999 and title is Article 999
    And another article with id 998 and status is draft and title is draft article
    And one more article with id 997 and is_removed is 1 and title is removed article
    And 6 articles
    When api request method is GET
    And api request path is /1.4/articles
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 7
    And api's response body field /data/0/id is 999
    And api's response body field /data/*/id does not contain 998
    And api's response body field /data/*/id does not contain 997
    And api's response body field /data/*/attributes/slug contains article-999
    And api's response body field /data/*/type is article
    And api's response body has field /data/*/attributes/title
    And api's response body has field /data/*/attributes/views_count

  Scenario: Filtering articles with "article" phrase in title in API 1.4
    Given article with id 999 and title is Article 999
    And 6 random instances of article
    When api request method is GET
    And api request path is /1.4/articles?title[phrase]=article
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 1
    And api's response body field /data/0/id is 999
    And api's response body field /data/0/attributes/slug is article-999
    And api's response body field /data/*/type is article
    And api's response body has field /data/*/attributes/title
    And api's response body has field /data/*/attributes/views_count

  Scenario: Filtering articles with "Dano trzecią potrawę" phrase in title in API 1.4
    Given 6 articles
    When api request method is GET
    And api request path is /1.4/articles?title[phrase]=Dano trzecią potrawę
    When send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 0

  Scenario: Article with id 999 in API 1.4
    Given article with id 999 and title is Article 999
    When api request method is GET
    And api request path is /1.4/articles/999
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/id is 999
    And api's response body field /data/attributes/slug is article-999
    And api's response body field /data/type is article
    And api's response body has field /data/attributes/title
    And api's response body has field /data/attributes/views_count

  Scenario: Article with id 999,article-999 in API 1.4
    Given article with id 999 and title is Article 999
    When api request method is GET
    And api request path is /1.4/articles/999,article-999
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/id is 999
    And api's response body field /data/attributes/slug is article-999
    And api's response body field /data/type is article
    And api's response body has field /data/attributes/title
    And api's response body has field /data/attributes/views_count


  Scenario: Article with id 999,does-not-exist-slug in API 1.4
    Given article with id 999 and title is Article 999
    When api request method is GET
    And api request path is /1.4/articles/999,does-not-exist-slug
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/id is 999
    And api's response body field /data/attributes/slug is article-999
    And api's response body field /data/type is article
    And api's response body has field /data/attributes/title
    And api's response body has field /data/attributes/views_count

  Scenario: Datasets listing for article 999 in API 1.4
    Given article with id 999 with 3 datasets
    When api request method is GET
    And api request path is /1.4/articles/999/datasets
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 3
    And api's response body field /data/*/type is dataset
    And api's response body has field /data/*/attributes/title
    And api's response body has field /data/*/attributes/views_count

  Scenario: Datasets listing for article 999,article-999 in API 1.4
    Given article with id 999 with 2 datasets
    When api request method is GET
    And api request path is /1.4/articles/999,article-999/datasets
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body field /data/*/type is dataset
    And api's response body has field /data/*/attributes/title
    And api's response body has field /data/*/attributes/views_count

  Scenario: Datasets listing for article 999,does-not-exist-slug in API 1.4
    Given article with id 999 with 2 datasets
    When api request method is GET
    And api request path is /1.4/articles/999,does-not-exist-slug/datasets
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 2
    And api's response body field /data/*/type is dataset
    And api's response body has field /data/*/attributes/title
    And api's response body has field /data/*/attributes/views_count



  Scenario: Article with id 1000 does not exist in API 1.4
    Given article with id 999 and title is Article 999
    When api request method is GET
    And api request path is /1.4/articles/1000
    And send api request and fetch the response
    Then api's response status code is 404
    And api's response body field /errors/0/code is 404_not_found

  Scenario: Listing with invalid field in GET in API 1.4
    Given 5 articles
    When api request method is GET
    And api request path is /1.4/articles?title[invalid_field]=invalid_value
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field /errors/0/source/pointer is /title/invalid_field
    And api's response body field /errors/0/code is 422_unprocessable_entity

  Scenario: Listing in API 1.4 with removed articles
    Given article with id 999 and title is Article 999
    And another article with id 998 and title is Another Article 998
    And one more article with id 997 and is_removed is 1 and title is removed article 997
    And 6 random instances of article
    When api request method is GET
    And api request path is /1.4/articles
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /meta/count is 8
    And api's response body field /data/*/id contains 999
    And api's response body field /data/*/id contains 998
    And api's response body field /data/*/id does not contain is 997
    And api's response body field /data/*/attributes/slug contains article-999
    And api's response body field /data/*/type is article
    And set status draft on article with id 998
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 7
    And restore article with id 997
    And send api request and fetch the response
    And api's response status code is 200
    And api's response body field /meta/count is 8
    And api's response body field /data/*/id contains 999
    And api's response body field /data/*/id does not contain 998
    And api's response body field /data/*/id contains 997


#  Scenario: Article view counter in API 1.4
#    Given article with id 999
#    And request method is GET
#    And api request path is /1.4/articles/999
#    When send api request and fetch the response
#    Then api's response status code is 200
#    And send api request and fetch the response
#    And 1 item views_count is 1
#    And send api request and fetch the response
#    And send api request and fetch the response
#    And send api request and fetch the response
#    And 1 item views_count is 4
#    And change request path to /1.4/articles
#    And send api request and fetch the response
#    And 1 item views_count is 5

  Scenario: Removed article is not accessable for not logged user in API 1.4
    Given removed article with id 999
    When api request method is GET
    And api request path is /1.4/articles/999
    And send api request and fetch the response
    Then api's response status code is 404

  Scenario: Draft article is not accessable for not logged user user in API 1.4
    Given draft article with id 999
    When api request method is GET
    And api request path is /1.4/articles/999
    And send api request and fetch the response
    Then api's response status code is 404

  Scenario: Removed article is not accessable for any user in API 1.4
    Given logged editor user
    Given removed article with id 999
    When api request method is GET
    And api request path is /1.4/articles/999
    And send api request and fetch the response
    Then api's response status code is 404


  Scenario: Draft article is not accessable for non-admin user in API 1.4
    Given logged editor user
    Given draft article with id 999
    When api request method is GET
    And api request path is /1.4/articles/999
    And send api request and fetch the response
    Then api's response status code is 404

  Scenario: Draft article is available for admin user in API 1.4
    Given logged admin user
    Given article with id 999 and status is draft and title is Article 999
    When api request method is GET
    And api request path is /1.4/articles/999
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/id is 999
    And api's response body field /data/attributes/slug is article-999
    And api's response body field /data/type is article
    And api's response body has field /data/attributes/title
    And api's response body has field /data/attributes/views_count

  Scenario: Test articles list is sortable by views_count ascendingly in API 1.4
    Given 3 articles
    When api request method is GET
    And api request path is /1.4/articles
    Then api request param sort is views_count
    And send api request and fetch the response
    And api's response list is sorted by views_count ascendingly

  Scenario: Test articles list is sortable by views_count descendingly in API 1.4
    Given 3 articles
    When api request method is GET
    And api request path is /1.4/articles
    Then api request param sort is -views_count
    And send api request and fetch the response
    And api's response list is sorted by views_count descendingly

  Scenario: Test articles list is sortable by views_count ascendingly in API 1.0
    Given 3 articles
    When api request method is GET
    And api request path is /1.0/articles
    Then api request param sort is views_count
    And send api request and fetch the response
    And api's response list is sorted by views_count ascendingly

  Scenario: Test articles list is sortable by views_count descendingly in API 1.0
    Given 3 articles
    When api request method is GET
    And api request path is /1.0/articles
    Then api request param sort is -views_count
    And send api request and fetch the response
    And api's response list is sorted by views_count descendingly

# TODO test other search queries
