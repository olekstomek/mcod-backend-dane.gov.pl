recommendations = {
    'io-error': 'Napraw ścieżkę, jeśli nie jest poprawna',
    'http-error': 'Napraw link URL, jeśli nie jest poprawny',
    'source-error': "- Napraw zawartość danych, np. zmień dane JSON na tablicę lub tablice/obiekty\n"
                    "- Ustaw poprawne ustawienia źródła w walidatorze.",
    'scheme-error': "- Napraw schemat danych, np. zmień schemat z FTP na HTTP (?)\n"
                    "- Ustaw poprawny schemat w walidatorze.",
    'format-error': "- Napraw format danych, np. zmień format z TXT na CSV\n"
                    "- Ustaw poprawny format w walidatorze.",
    'encoding-error': "Napraw źródło danych, jeśli jest uszkodzone.\n"
                      " - Ustaw poprawne kodowanie w walidatorze.",
    'blank-header': "Dodaj brakującą nazwę kolumny do pierwszego wiersza źródła danych.\n"
                    "- Jeśli pierwszy wiersz zaczyna się od lub kończy przecinkiem, usuń go.\n"
                    "- Aby zignorować błąd, wyłącz sprawdzanie `puste nagłówki` w walidatorze.",
    'duplicate-header': "Dodaj brakującą nazwę kolumny do pierwszego wiersza danych.\n"
                        "- Jeśli pierwszy wiersz zaczyna się od, lub kończy przecinkiem, usuń go.\n"
                        "- Aby zignorować błąd, wyłącz sprawdzanie \"zduplikowany nagłówek\" w walidatorze.",
    'blank-row': "Usuń wiersz.\n"
                 "- Aby zignorować błąd, wyłącz sprawdzanie \"pusty wiersz\" w walidatorze.",
    'duplicate-row': "Jeśli niektóre dane są niepoprawne, popraw je.\n"
                     "- Jeśli cały wiersz jest niepoprawnie zduplikowany, usuń go.\n"
                     "- Aby zignorować błąd, wyłącz sprawdzanie `zduplikowany wiersz` w walidatorze.",
    'extra-value': "Sprawdź, czy dane zawierają dodatkowy przecinek między wartościami w tym wierszu.\n"
                   "- Aby zignorować błąd, wyłącz  sprawdzanie wartości dodatkowej w walidatorze",
    'missing-value': "Sprawdź, czy w danych nie brakuje przecinka między wartościami w tym wierszu.\n"
                     "- Aby zignorować błąd, wyłącz sprawdzanie \"brakującej wartości\" w walidatorze.",
    'schema-error': "Zaktualizuj deskryptor schematu żeby stał się poprawny\n"
                    "- Aby zignorować błąd, wyłącz sprawdzanie schematu w walidatorze.",
    'non-matching-header': "Zmień nazwę nagłówka w źródle danych lub nazwe pola w schemacie\n"
                           "- Aby zignorować błąd, wyłącz sprawdzanie \"nie pasującego nagłówka\" w walidatorze.",
    'extra-header': "Usuń dodatkową kolumnę ze źródła danych lub dodaj brakujące pole do schematu\n"
                    "- Aby zignorować bład, wyłącz sprawdzanie \"dodatkowego nagłówka\" w walidatorze.",
    'missing-header': "Dodaj brakującą kolumnę do źródła danych lub usuń dodatkowe pole ze schematu\n"
                      "- Aby zignorować błąd, wyłącz sprawdzanie  \"brakujący nagłówek\" w walidatorze.",
    'type-or-format-error': "- Jeśli ta wartość nie jest poprawna, zaktualizuj wartość.\n"
                            "- Jeśli ta wartość jest prawidłowa, dostosuj typ i / lub format.\n"
                            "- Aby zignorować błąd, wyłącz sprawdzanie \"błąd typu lub formatu\" w walidatorze.\n"
                            "W takim przypadku wszystkie sprawdzenia schematu dla wartości wierszy będą ignorowane.",
    'required-constraint': "- Jeśli ta wartość nie jest poprawna, zaktualizuj wartość.\n"
                           "- Jeśli wartość jest prawidłowa, usuń ograniczenie \"wymagalność\" ze schematu.\n"
                           "- Jeśli ten błąd powinien być ignorowany, wyłącz sprawdzanie `wymagalność' w walidatorze.",
    'pattern-constraint': "- Jeśli ta wartość nie jest poprawna, zaktualizuj wartość.\n"
                          "- Jeśli wartość jest prawidłowa, usuń lub zmień ograniczenie  \"wzorzec\" w schemacie.\n"
                          "- Jeśli ten błąd powinien zostać zignorowany, wyłącz sprawdzanie \"wzorca\" w walidatorze.",
    'unique-constraint': "- Jeśli ta wartość nie jest poprawna, zaktualizuj wartość.\n"
                         "- Jeśli wartość jest poprawna , wartości w tej kolumnie nie są unikalne. Usuń ograniczenie"
                         "\"unikalność\" ze schematu.\n"
                         "- Jeśli ten błąd powinien zostać zignorowany, wyłącz sprawdzanie \"unikalność\""
                         " w walidatorze.",
    'enumerable-constraint': "- Jeśli ta wartość nie jest poprawna, zaktualizuj wartość.\n"
                             "- Jeśli wartość jest prawidłowa, usuń lub zmień ograniczenie \"enum\" w schemacie.\n"
                             "- Jeśli ten błąd powinien zostać zignorowany, wyłącz sprawdzenie \"enumeracja\" "
                             "w walidatorze.",
    'minimum-constraint': "- Jeśli ta wartość nie jest poprawna, zaktualizuj wartość.\n"
                          "- Jeśli wartość jest prawidłowa, usuń lub zmien wartosć minimalną w schemacie.\n"
                          "- Jeśli ten błąd powinien być ignorowany, wyłącz sprawdzenie \"wartości minimalnej\""
                          "w walidatorze.",
    'maximum-constraint': "- Jeśli ta wartość nie jest poprawna, zaktualizuj wartość.\n"
                          "- Jeśli wartość jest prawidłowa, usuń lub zmień  wartość maksymalną w schemacie.\n"
                          "- Jeśli błąd ten powinien zostać zignorowany, należy wyłączyć sprawdzanie \"wartości "
                          "maksymalnej\" w walidatorze.",
    'minimum-length-constraint': "- Jeśli ta wartość nie jest poprawna, zaktualizuj wartość.\n"
                                 "- Jeśli wartość jest prawidłowa, usuń lub zmień ograniczenie \"długość minimalna\" "
                                 "w schemacie.\n"
                                 "- Jeśli ten błąd powinien być ignorowany, wyłącz sprawdzanie \"długości minimalnej\" "
                                 "w walidatorze.",
    'maximum-length-constraint': "- Jeśli ta wartość nie jest poprawna, zaktualizuj wartość.\n"
                                 "- Jeśli wartość jest prawidłowa, usuń lub zmień ograniczenie \"długość maksymalna\" "
                                 "w schemacie.\n"
                                 "- Jeśli błąd ten powinien zostać zignorowany, wyłącz sprawdzanie ograniczenia "
                                 "\"długości maksymalnej\" w walidatorze.",

    'FileNotFoundError': "Sprawdź czy plik istnieje we wskazanej lokalizacji.",
    'connection-error': "Spróbuj ponownie później.",
    'UnknownFileFormatError': "Sprawdź czy format pliku jest zgodny ze standardem technicznym.",
    'unknown-encoding': "Sprawdź czy kodowanie znaków w pliku jest zgodne z ISO-8859-2, Windows-1250, CP852, UTF-8. "
                        "Zmień kodowanie polskich znaków na UTF-8.",
    'UnsupportedArchiveError': 'Kompresja jest dopuszczalna dla pojedynczego pliku lub dla plików typu shapefile',

    'location-moved': "Sprawdź czy podany link poprawnie wskazuje na zasób.",
    '400-bad-request': "Sprawdź czy podany link jest poprawnie wpisany.",
    '403-forbidden': "Sprawdź czy podany link jest poprawnie wpisany.",
    "404-not-found": "Sprawdź lokalizację zasobu.",
    '503-service-unavailable': "Spróbuj ponownie później.",
    "connection-aborted": "Spróbuj ponownie później.",
    'ReadTimeout': 'Sprawdź czy podany link poprawnie wskazuje na zasób.',
    'SSLError': "Skontaktuj się z administratorem.",
    'InvalidSchema': "Sprawdź czy podany link jest poprawnie wpisany.",
    'InvalidUrl': "Sprawdź czy podany link jest poprawnie wpisany.",
    'InvalidContentType': 'Sprawdź poprawność adresu url',

    None: ""
}

messages = {
    'unknown-encoding': "Nierozpoznane kodowanie polskich znaków.",
    'UnknownFileFormatError': "Nierozpoznany format pliku.",
    'no-file-associated': "Zasób nie ma przypisanego pliku.",
    'connection-error': "Nie udało się nawiązać połączenia.",
    'FileNotFoundError': "Brak pliku we wskazanej lokalizacji.",
    'UnsupportedArchiveError': 'Niedopuszczalna kompresja plików',

    'location-moved': "Lokalizacja zasobu została zmieniona.",
    '400-bad-request': "Nieprawidłowe sformułowanie zapytania (wywołania) – żądanie nie może być obsłużone przez "
                       "serwer z powodu nieprawidłowości identyfikowanej jako błąd użytkownika (np. literówki w "
                       "adresie WWW).",
    '403-forbidden': "Brak dostępu - aby wejść na daną witrynę należy uzyskać prawo dostępu, a jeśli jest to "
                     "witryna ogólnodostępna, należy skontaktować się z administratorem sieci. Błąd może też "
                     "oznaczać nieaktualne łącze, niedostępne już w witrynie web.",
    "404-not-found": "Nie znaleziono zasobu – serwer nie odnalazł zasobu według podanego linku.",
    "503-service-unavailable": "Strona o podanym adresie jest obecnie niedostępna.",
    "connection-aborted": "Połączenie zostało przerwane w trakcie walidacji.",
    'ReadTimeout': 'Limit czasu odczytu został przekroczony',
    'SSLError': "Weryfikacja certyfikatu SSL nie powiodła się.",
    'InvalidSchema': "Niepoprawny protokół w podanym adresie URL.",
    'InvalidUrl': "Niepoprawny adres URL.",
    'InvalidResponseCode': "Nieprawidłowy kod odpowiedzi",
    'InvalidContentType': 'Nieobsługiwany typ',
    'failed-new-connection': "Nie można ustanowić nowego połączenia. Nazwa lub usługa nieznana.",
    None: ""
}
