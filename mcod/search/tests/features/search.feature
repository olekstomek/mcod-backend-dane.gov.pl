@elasticsearch
Feature: Global Search API
  Scenario: Test that endpoint returns english message about too short search phrase
    Given institution with id 777 and 2 datasets
    When api request method is GET
    And api request path is /1.4/search/
    And api request language is en
    And api request param q is a
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field /errors/[0]/detail is The entered phrase should be at least 2 characters long

  Scenario: Test that endpoint returns polish message about too short search phrase
    Given institution with id 777 and 2 datasets
    When api request method is GET
    And api request path is /1.4/search/
    And api request language is pl
    And api request param q is c
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field /errors/[0]/detail is Wpisana fraza musi zawierać przynajmniej 2 znaki

  Scenario Outline: Test that search returns valid response for different queries
    Given <object_type> created with params <params>
    When api request method is GET
    And api request path is /1.4/search/
    And api request param per_page is 100
    And api request has params <req_params>
    And api request language is <lang_code>
    Then send api request and fetch the response
    And api's response status code is 200
    And api's search response objects have fields <fields_str>

    Examples:
    | object_type | params                                       | req_params                                    | lang_code | fields_str                                        |
    | application | {"id": 999, "title_en": "title_en"}          | {"model": "application", "q": "title_en"}     | en        | title,notes,author,image_thumb_url,image_alt      |
    | application | {"id": 999, "title": "title_pl"}             | {"model": "application", "q": "title_pl"}     | pl        | title,notes,author,image_thumb_url,image_alt      |
    | application | {"id": 999, "notes_en": "notes_en"}          | {"model": "application", "q": "notes_en"}     | en        | title,notes,author,image_thumb_url,image_alt      |
    | application | {"id": 999, "notes": "notes_pl"}             | {"model": "application", "q": "notes_pl"}     | pl        | title,notes,author,image_thumb_url,image_alt      |
    | application | {"id": 999, "author": "John Cleese"}         | {"model": "application", "q": "John Cleese"}  | en        | title,notes,author,image_thumb_url,image_alt      |
    | application | {"id": 999, "author": "John Cleese"}         | {"model": "application", "q": "John Cleese"}  | pl        | title,notes,author,image_thumb_url,image_alt      |
    | application | {"id": 999, "tags": ["app_tag_en"]}          | {"model": "application", "q": "app_tag_en"}   | en        | title,notes,author,image_thumb_url,image_alt,tags |
    | application | {"id": 999, "tags": ["app_tag_pl"]}          | {"model": "application", "q": "app_tag_pl"}   | pl        | title,notes,author,image_thumb_url,image_alt,tags |

    | article     | {"id": 999, "title_en": "title_en"}          | {"model": "article", "q": "title_en"}         | en        | title,notes              |
    | article     | {"id": 999, "title": "title_pl"}             | {"model": "article", "q": "title_pl"}         | pl        | title,notes              |
    | article     | {"id": 999, "notes_en": "notes_en"}          | {"model": "article", "q": "notes_en"}         | en        | title,notes              |
    | article     | {"id": 999, "notes": "notes_pl"}             | {"model": "article", "q": "notes_pl"}         | pl        | title,notes              |
    | article     | {"id": 999, "tags": ["article_tag_en"]}      | {"model": "article", "q": "article_tag_en"}   | en        | title,notes,tags         |
    | article     | {"id": 999, "tags": ["article_tag_pl"]}      | {"model": "article", "q": "article_tag_pl"}   | pl        | title,notes,tags         |

    | dataset     | {"id": 999, "title_en": "ds_title_en"}       | {"model": "dataset", "q": "ds_title_en"}      | en        | title,notes              |
    | dataset     | {"id": 999, "title": "ds_title_pl"}          | {"model": "dataset", "q": "ds_title_pl"}      | pl        | title,notes              |
    | dataset     | {"id": 999, "notes_en": "ds_notes_en"}       | {"model": "dataset", "q": "ds_notes_en"}      | en        | title,notes              |
    | dataset     | {"id": 999, "notes": "ds_notes_pl"}          | {"model": "dataset", "q": "ds_notes_pl"}      | pl        | title,notes              |
    | dataset     | {"id": 999, "tags": ["ds_tag_en"]}           | {"model": "dataset", "q": "ds_tag_en"}        | en        | title,notes,tags         |
    | dataset     | {"id": 999, "tags": ["ds_tag_pl"]}           | {"model": "dataset", "q": "ds_tag_pl"}        | pl        | title,notes,tags         |

    | resource    | {"id": 999, "title_en": "res_title_en"}      | {"model": "resource", "q": "res_title_en"}    | en        | title,notes              |
    | resource    | {"id": 999, "title": "res_title_pl"}         | {"model": "resource", "q": "res_title_pl"}    | pl        | title,notes              |
    | resource    | {"id": 999, "description_en": "res_desc_en"} | {"model": "resource", "q": "res_desc_en"}     | en        | title,notes              |
    | resource    | {"id": 999, "description": "res_desc_pl"}    | {"model": "resource", "q": "res_desc_pl"}     | pl        | title,notes              |

    | institution | {"id": 999, "title_en": "ins_title_en"}      | {"model": "institution", "q": "ins_title_en"} | en        | title,notes,abbreviation |
    | institution | {"id": 999, "title": "ins_title_pl"}         | {"model": "institution", "q": "ins_title_pl"} | pl        | title,notes,abbreviation |
    | institution | {"id": 999, "description_en": "ins_desc_en"} | {"model": "institution", "q": "ins_desc_en"}  | en        | title,notes,abbreviation |
    | institution | {"id": 999, "description": "ins_desc_pl"}    | {"model": "institution", "q": "ins_desc_pl"}  | pl        | title,notes,abbreviation |
    | institution | {"id": 999, "abbreviation": "abbrev"}        | {"model": "institution", "q": "abbrev"}       | en        | title,notes,abbreviation |
    | institution | {"id": 999, "abbreviation": "abbrev"}        | {"model": "institution", "q": "abbrev"}       | pl        | title,notes,abbreviation |
