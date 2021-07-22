Feature: Resources openness scores are set properly

  Scenario: Resource score is inreased and newly created csv file has headers from xls file
    Given resource with id 999 and xls file converted to csv
    Then resource csv file has 0,First Name,Last Name,Gender,Country,Age,Date,Id as headers
    And resources.Resource with id 999 contains data {"openness_score": 3}

  Scenario Outline: Created resource with tiff file has proper openness score and format
    Given resource with <filename> file and id <obj_id>
    Then <object_type> with id <obj_id> contains data <data_str>

    Examples:
    | obj_id | object_type        | filename             | data_str                                                                                      |
    | 1000   | resources.Resource |cea.tif               | {"openness_score": 3, "format": "geotiff", "file_mimetype": "image/tiff;application=geotiff"} |
    | 1000   | resources.Resource |tiff_and_tfw.zip      | {"openness_score": 3, "format": "geotiff", "file_mimetype": "image/tiff;application=geotiff"} |
    | 1000   | resources.Resource |single_geotiff.zip    | {"openness_score": 3, "format": "geotiff", "file_mimetype": "image/tiff;application=geotiff"} |
    | 1000   | resources.Resource |sample_TIFF_file.tiff | {"openness_score": 1, "format": "tiff", "file_mimetype": "image/tiff"}                        |
