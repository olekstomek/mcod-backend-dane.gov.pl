Feature: File validation

  Scenario Outline: Validation of various file types
    Given I have file <file_type>
    Then file is validated and result is <file_format>
    Examples:
    | file_type                 | file_format |
    | docx                      | docx        |
    | geojson                   | geojson     |
    | geojson without extension | geojson     |
    | json with geojson content | geojson     |
    | ods                       | ods         |
    | xlsx                      | xlsx        |
    | zip with one csv          | csv         |
    | tar.gz with one csv       | csv         |
    | shapefile arch            | shp         |
    | gpx                       | gpx         |
    | grib                      | grib        |
    | hdf_netcdf                | nc          |
    | binary_netcdf             | nc          |
    | cp1251.dbf                | dbf         |
    | dbase_03.dbf              | dbf         |
    | dbase_30.dbf              | dbf         |
    | dbase_31.dbf              | dbf         |
    | dbase_83.dbf              | dbf         |
    | dbase_83_missing_memo.dbf | dbf         |
    | dbase_8b.dbf              | dbf         |
    | dbase_f5.dbf              | dbf         |
    | kml                       | kml         |

  Scenario Outline: Validation of rar with many files
    Given I have file <file_type>
    Then file is validated and UnsupportedArchiveError is raised
    Examples:
    | file_type           |
    | rar with many files |
    | zip with many files |

  Scenario Outline: Validation of various file mimetypes
    Given I have file <file_type>
    Then file is validated and result mimetype is <mimetype>
    Examples:
    | file_type       | mimetype           |
    | grib            | application/x-grib |
    | hdf_netcdf      | application/netcdf |
    | binary_netcdf   | application/netcdf |
