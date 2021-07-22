Feature: Increasing resource openness
  Scenario: Resource newly created csv file has headers from xls file
    Given resource with id 999 and xls file converted to csv
    Then resource csv file has 0,First Name,Last Name,Gender,Country,Age,Date,Id as headers