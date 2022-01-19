Feature: Resource forms
  Scenario: Maps and plots correct set
    Given form class is mcod.resources.forms.ChangeResourceForm
    And form instance is geo_tabular_data_resource
    And form geo data is {"geo_0": "label", "geo_2": "l", "geo_3": "b"}
    Then form is valid

  Scenario Outline: Map and plots invalid sets
    Given form class is mcod.resources.forms.ChangeResourceForm
    And form instance is tabular_resource
    And form tabular data is <form_data>
    Then form field <field> error is <error>
    Examples:
    | form_data                                          | field          | error                                                                                                                                                                                  |
    | {"geo_1": "l", "geo_2": "b"}                       | maps_and_plots | Brak elementów: etykieta dla zestawu danych mapowych: współrzędne geograficzne. Ponów definiowanie mapy wybierając wskazane elementy.                                                  |
    | {"geo_1": "uaddress"}                              | maps_and_plots | Brak elementów: etykieta dla zestawu danych mapowych: adres uniwersalny. Ponów definiowanie mapy wybierając wskazane elementy.                                                         |
    | {"geo_1": "place", "geo_2": "postal_code"}         | maps_and_plots | Brak elementów: etykieta dla zestawu danych mapowych: adres. Ponów definiowanie mapy wybierając wskazane elementy.                                                                     |
    | {"geo_1": "label"}                                 | maps_and_plots | Zestaw danych mapowych jest niekompletny                                                                                                                                               |
    | {"geo_1": "label", "geo_2": "label", "geo_3": "b"} | maps_and_plots | element etykieta wystąpił więcej niż raz. Ponów definiowanie mapy wybierając tylko raz wymagany element zestawu mapowego.                                                              |
    | {"geo_1": "place", "geo_2": "b"}                   | maps_and_plots | pochodzą z różnych zestawów danych mapowych. Ponów definiowanie mapy wybierając elementy z tylko jednego zestawu danych mapowych. |
