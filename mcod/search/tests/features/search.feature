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

    | showcase    | {"id": 999, "title_en": "title_en"}          | {"model": "showcase", "q": "title_en"}     | en        | title,notes,author,image_thumb_url,image_alt,showcase_category,showcase_category_name,showcase_platforms,showcase_types      |
    | showcase    | {"id": 999, "title": "title_pl"}             | {"model": "showcase", "q": "title_pl"}     | pl        | title,notes,author,image_thumb_url,image_alt,showcase_category,showcase_category_name,showcase_platforms,showcase_types      |
    | showcase    | {"id": 999, "notes_en": "notes_en"}          | {"model": "showcase", "q": "notes_en"}     | en        | title,notes,author,image_thumb_url,image_alt,showcase_category,showcase_category_name,showcase_platforms,showcase_types      |
    | showcase    | {"id": 999, "notes": "notes_pl"}             | {"model": "showcase", "q": "notes_pl"}     | pl        | title,notes,author,image_thumb_url,image_alt,showcase_category,showcase_category_name,showcase_platforms,showcase_types      |
    | showcase    | {"id": 999, "author": "John Cleese"}         | {"model": "showcase", "q": "John Cleese"}  | en        | title,notes,author,image_thumb_url,image_alt,showcase_category,showcase_category_name,showcase_platforms,showcase_types      |
    | showcase    | {"id": 999, "author": "John Cleese"}         | {"model": "showcase", "q": "John Cleese"}  | pl        | title,notes,author,image_thumb_url,image_alt,showcase_category,showcase_category_name,showcase_platforms,showcase_types      |
    | showcase    | {"id": 999, "tags": ["app_tag_en"]}          | {"model": "showcase", "q": "app_tag_en"}   | en        | title,notes,author,image_thumb_url,image_alt,tags,showcase_category,showcase_category_name,showcase_platforms,showcase_types |
    | showcase    | {"id": 999, "tags": ["app_tag_pl"]}          | {"model": "showcase", "q": "app_tag_pl"}   | pl        | title,notes,author,image_thumb_url,image_alt,tags,showcase_category,showcase_category_name,showcase_platforms,showcase_types |

  Scenario Outline: Search filters by regions geodata
    Given dataset with id 998
    And resource with id 999 dataset id 998 and single main region
    And 3 resources
    When api request method is GET
    And api request path is <request_path>
    Then send api request and fetch the response
    And api's response status code is 200
    And has assigned Polska,Warszawa as name for regions
    And has assigned 85633723,101752777 as region_id for regions

      Examples:
      | request_path                                                                                                    |
      | /1.4/search/?regions[bbox][geo_shape]=19.259214,53.481806,23.128409,51.013112&model[terms]=resource&per_page=10 |
      | /1.4/search/?regions[id][terms]=101752777&model[terms]=resource&per_page=10                                     |

  Scenario Outline: Institution abbrevation based search is case insensitive
    Given institution created with params {"id": 1000, "title": "test institution", "slug": "test-institution", "abbreviation": "TSTI"}
    When api request path is <request_path>
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field data/[0]/attributes/title is test institution

    Examples:
      | request_path                                                                  |
      | /1.4/search?page=1&per_page=20&q=tsti&sort=relevance&model[terms]=institution |
      | /1.4/search?page=1&per_page=20&q=TSTI&sort=relevance&model[terms]=institution |
      | /1.4/search?page=1&per_page=20&q=TSti&sort=relevance&model[terms]=institution |

  Scenario: Search filtered facet returns region aggregation
    Given dataset with id 998
    And resource with id 999 dataset id 998 and single main region
    And 3 resources
    When api request method is GET
    And api request path is /1.4/search?model[terms]=dataset,resource&per_page=1&filtered_facet[by_regions]=101752777
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response body field meta/aggregations/by_regions/[0]/id is 101752777
    And api's response body field meta/aggregations/by_regions/[0]/title is Warszawa, Gmina Warszawa, pow. Warszawa, woj. Mazowieckie
