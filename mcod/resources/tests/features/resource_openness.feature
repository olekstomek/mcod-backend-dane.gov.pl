Feature: Resources openness scores are set properly

  Scenario: Resource score is increased and newly created csv file has headers from xls file
    Given resource with id 999 and xls file converted to csv
    Then resource csv file has 0,First Name,Last Name,Gender,Country,Age,Date,Id as headers
    And resources.Resource with id 999 contains data {"openness_score": 3}

  Scenario Outline: Created resource with file has proper openness score and format
    Given resource with <filename> file and id <obj_id>
    Then <object_type> with id <obj_id> contains data <data_str>

    Examples:
    | obj_id | object_type        | filename                 | data_str                                                                                           |
    | 1000   | resources.Resource |cea.tif                   | {"openness_score": 3, "format": "geotiff", "main_file_mimetype": "image/tiff;application=geotiff"} |
    | 1000   | resources.Resource |tiff_and_tfw.zip          | {"openness_score": 3, "format": "geotiff", "main_file_mimetype": "image/tiff;application=geotiff"} |
    | 1000   | resources.Resource |single_geotiff.zip        | {"openness_score": 3, "format": "geotiff", "main_file_mimetype": "image/tiff;application=geotiff"} |
    | 1000   | resources.Resource |sample_TIFF_file.tiff     | {"openness_score": 1, "format": "tiff", "main_file_mimetype": "image/tiff"}                        |
    | 1000   | resources.Resource |linked_rdf.rdf            | {"openness_score": 5, "format": "rdf"}                                                             |
    | 1000   | resources.Resource |linked_jsonld.jsonld      | {"openness_score": 5, "format": "jsonld"}                                                          |
    | 1000   | resources.Resource |linked_nt.nt              | {"openness_score": 5, "format": "nt"}                                                              |
    | 1000   | resources.Resource |csv2jsonld.jsonld         | {"openness_score": 4, "format": "jsonld"}                                                          |
    | 1000   | resources.Resource |plik_nq.nq                | {"openness_score": 4, "format": "nq"}                                                              |
    | 1000   | resources.Resource |zlinkowany_plik_nq.nq     | {"openness_score": 5, "format": "nq"}                                                              |
