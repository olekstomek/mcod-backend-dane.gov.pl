Feature: File validation

  Scenario: Validation of docx file
    Given I have docx file
    Then file is validated and result is docx

  Scenario: Validation of ods file
    Given I have ods file
    Then file is validated and result is ods

  Scenario: Validation of xlsx file
    Given I have xlsx file
    Then file is validated and result is xlsx

  Scenario: Validation of rar with many files
    Given I have rar with many files
    Then file is validated and UnsupportedArchiveError is raised

  Scenario: Validation of zip with one file
    Given I have zip with one csv file
    Then file is validated and result is csv

  Scenario: Validation of zip with many files
    Given I have zip with many files
    Then file is validated and UnsupportedArchiveError is raised
