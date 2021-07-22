Feature: Dataset Comment

  Scenario Outline: Commenting for dataset works fine
    Given dataset with id 999
    And list of sent emails is empty
    When api request method is POST
    And api request header <req_header_name> is <req_header_value>
    And api request path is /1.4/datasets/999/comments
    And api request posted data is {"data": {"type": "comment", "attributes": {"comment": "Some comment for dataset 999."}}}
    And send api request and fetch the response
    Then api's response status code is 201
    And api's response body field data/attributes/comment is Some comment for dataset 999.
    And sent email contains Some comment for dataset 999.
    And sent email contains <text>

    Examples:
    | req_header_name | req_header_value | text                                 |
    # For now only PL translated emails are sent.
    # | Accept-Language | en               | A comment was posted on the data set |
    | Accept-Language | en               | Zgłoszono uwagę do zbioru            |
    | Accept-Language | pl               | Zgłoszono uwagę do zbioru            |
