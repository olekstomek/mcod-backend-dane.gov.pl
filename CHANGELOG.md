# CHANGELOG



## Unreleased
---

### New

### Changes

### Fixes

### Breaks


## 2.31.5 - (2023-03-30)
---

### Fixes
* Poprawa walidacji serializera w zakresie warunków ponownego wykorzystania informacji (OTD-39)


## 2.31.4 - (2023-03-21)
---

### Fixes
* Blokada dodawania warunków - incydent krytyczny (OTD-28)
* Poprawa walidacji formularza oraz serializera w zakresie warunków ponownego wykorzystania informacji (OTD-30)
* Poprawki zgłoszone przez administratorów po wydaniu na produkcję (OTD-34)


## 2.31.3 - (2023-02-27)
---

### Fixes
* Naprawa createsuperuser (OTD-11)
* Naprawa błędów testów uruchamianych lokalnie (PBR-106)
* Naprawa błędów budowania CI (PBR-123)
* Podniesienie wersji paczek Pythonowych (PBR-123)


## 2.31.2 - (2022-08-30)
---

## 2.31.1 - (2022-08-30)
---

## 2.31.0 - (2022-08-25)
---

## 2.30.0 - (2022-08-17)
---

## 2.29.0 - (2022-08-02)
---

## 2.28.0 - (2022-07-21)
---

## 2.27.0 - (2022-06-29)
---

## 2.26.0 - (2022-06-01)
---

## 2.25.0 - (2022-05-12)
---

## 2.24.0 - (2022-04-21)
---

## 2.23.0 - (2022-03-28)
---

## 2.22.0 - (2022-03-10)
---

## 2.21.0 - (2022-02-15)
---

## 2.20.0 - (2022-01-17)
---

## 2.19.0 - (2021-12-08)
---

## 2.18.0 - (2021-11-16)
---

## 2.17.0 - (2021-10-26)
---

## 2.16.0 - (2021-09-07)
---

## 2.15.0 - (2021-06-14)
---

## 2.14.0 - (2021-05-24)
---

## 2.13.0 - (2021-05-05)
---

## 2.12.0 - (2021-04-13)
---

## 2.11.1 - (2021-03-17)
---

## 2.11.0 - (2021-03-15)
---

## 2.10.0 - (2021-02-24)
---

## 2.9.0 - (2021-02-01)
---

## 2.8.1 - (2020-12-29)
---

## 2.8.0 - (2020-12-15)
---

## 2.7.0 - (2020-12-01)
---

## 2.6.0 - (2020-10-18)
---

## 2.5.0 - (2020-09-30)
---

## 2.4.0 - (2020-09-07)
---

## 2.3.1 - (2020-08-11)
---

## 2.3.0 - (2020-07-29)
---

## 2.2.1 - (2020-07-03)
---

## 2.2.0 - (2020-06-29)
---

## 2.1.1 - (2020-06-17)
---

## 2.1.0 - (2020-05-28)
---

## 2.0.0 - (2020-05-11)
---

## 1.18.0 - (2020-05-04)
---

## 1.17.0 - (2020-03-16)
---

## 1.16.0 - (2020-03-09)
---

## 1.15.1 - (2020-02-18)
---

## 1.15.0 - (2020-02-18)
---

## 1.14.0 - (2020-01-22)
---

## 1.13.0 - (2019-12-18)
---

## 1.12.1 - (2019-11-28)
---

## 1.12.0 - (2019-11-25)
---

## 1.11.0 - (2019-09-25)
---

### New
* Możliwość zmiany statusu wszystkim notyfikacjom (MCOD-1605, MCOD-1632)
* Migracja końcówek artykułów na API 1.4 (MCOD-1641)
* Migracja strony gównej do API 1.4 (MCOD-1630)
* Narzędzie do modyfikacji schematu zasobu (MCOD-1591, MCOD-1617)
* Raporty mailowe z aktywności w obserwowanych obiektach (MCOD-824, MCOD-1631)
* Newsletter (MCOD-1280, MCOD-1645, MCOD-1673, MCOD-1629, MCOD-1670, MCOD-1671)

### Changes
* Zmiana koloru przycisku "Zgłoś uwagi" (MCOD-1573)
* Zmiany tekstów związanych z rejestracją użytkownika (MCOD-1654)


### Fixes
* Poprawki w dokumentacji API (MCOD-1323)
* Usunięcie nieużywanych końcówek typu autocomplete (MCOD-1675)
* Poprawki związane z przyszłym wdrożeniem modułu CMS
* Inne drobne poprawki w PA


## 1.10.1 - (2019-09-05)
---

## 1.10.0 - (2019-09-04)
---

## 1.9.0 - (2019-06-14)
---

### New
* Implementacja w API 1.4 obsługi użytkownika (konto, zmiana hasła, logowanie i tp) (MCOD-1481)
* Konwersja plików  SHP do GeoJSON (MCOD-1469)
* Indeksowanie danych geograficznych w Elasticsearchu (MCOD-1470)
### Changes
* Weryfikacja pierwszej kolumny zasobu na zgodność z formatem numerycznym (MCOD-1489)
* Rozszerzenie historii wyszukiwania użytkownika o instytucje, materiały edukacyjne, pomoc. (MCOD-1505)
### Fixes
* Poprawka do zasobów spakowanych zawierajacych więcej niż jeden plik (MCOD-1507)
* Poprawka do wyświetlania formatu .ods jako True (MCOD-1406)
* Poprawka tekstu w treści maila (MCOD-1494)
* Poprawka wyników wyszukiwania w API 1.4 (MCOD-1530)


## 1.8.0 - (2019-06-14)
---

### New
* Obsługa slug'ów we wszystkich obiektach API (MCOD-1325)
* Nowa końcówka API do pobierania zasobu (MCOD-1428)
* (WIP) Narzędzie dla dostawców do walidacji zasobów (MCOD-1455)
* Rozszerzenie mechanizmu walidacji zasobów o nowe komunikaty o błędach (MCOD-1501)
* 
### Changes
* migracja kolejnych końcówek API do wersji 1.4
* dostosowanie formatu odpowiedzi w przypadku błędów do Json:API

### Fixes
* Poprawki związane z błędnym działanie liczników wyświetleń oraz pobrań (MCOD-1510, MCOD-1518)
* Poprawki związane z błędnym generowaniem slug'ów dla zbiorów danych


## 1.7.0 - (2019-05-30)
---

### New
* Nowy mechanizm synchronizacji danych po walidacji zasobów (MCOD-1042)
* Podstawowa obsługa plików SHP (MCOD-1276)
* Prezentacja wyników walidacji zasobów ze szczegółową informacją o błędach (MCOD-1281)
* Prezentacja wyników walidacji danych tabelarycznych (MCOD-1344)
* Możliwość zgłaszania uwag do zasobu (MCOD-1359)
* Możliwość zgłaszania zapotrzebowania na nowe zasoby (MCOD-1360)
* Obsługa slug'ów objektu po stronie API (MCOD-1364)

### Changes
* Zmiany w prezentacji wyników walidacji linku do zasobu (MCOD-1414)
* Zmiany w prezentacji wyników walidacji pliku zasobu (MCOD-1413)
* Aktualizacja modułów i komponentów backendu do nowszych wersji (m. innymi Falcon 2.0)
* Aktualizacje końcówek API do wersji 1.4

### Fixes
* Poprawki do wyświetlania zbiorów bez przydzielonej kategorii (MCOD-1368)
* Optymalizacja zapytań do bazy (MCOD-1422)
* Inne drobne poprawki


## 1.6.0 - (2019-04-24)
---

### New
* Nowy zestaw pól z datami w zasobie oraz zbiorze (MCOD-1192)
* Integracja z Hashocorp Vault (MCOD-1207)
* Obsługa skompresowanych archiwów (MCOD-1072)
* Obsługa plików DBF (MCOD-1343)
* Obsługa wielojęzyczności w zasobach, zbiorach i innych (MCOD-1303)
* Obsługa wersjonowania API za pomocą ścieżki (MCOD-1324)
* Integracja z ElasticAPM (MCOD-1210)

### Changes
* Zmiany wyświetlania numerów telefonów poprzez końcówkę API (MCOD-1320)
* Migracja na Django 2.2 (MCOD-1210)

### Fixes
* Poprawki do nawigacji w PA (MCOD-855)
* Zbyt restrykcyjna walidacja na nr telefonu organizacji (MCOD-1337)
* Poprawki w wyświetlaniu wyników walidacji zasobów (MCOD-1335)
* Różne drobne poprawki końcówek API (MCOD-1323)
* Poprawki w szablonach wyświetlających listę zasobów (MCOD-1324, MCOD-1356)
* Poprawki błędów 500 w sortowaniu wyników na końcówkach API (MCOD-1348)
* Poprawki błędów 500 podczas zgłaszania uwag do zbioru (MCOD-1397)


## 1.5.0 - (2019-03-12)
---

### New
* Narzędzia do obsługi dziennika wersji
* Dodatkowe filtry wyszukiwania w panelu administratora (MCOD-993)
* Eksport zasobów wraz z powiazanymi danymi do pliku CSV (MCOD-1261)
* Rozdzielenie bazy wiedzy oraz aktualności (MCOD-1200)

### Changes
* Usunięcie możliwości edycji dla pola licencji (MCOD-1012)
* Brakujące tłumaczenia w formularzu do dodawania użytkownika (MCOD-1016)
* Usunięcie kolumny name na liście instytucji (MCOD-1221)

### Fixes
* Poprawki literówek w panelu administracyjnym (MCOD-1334)
* Poprawki w historii wyszukiwania (MCOD-933)
* Poprawki do wyświetlania liczby aktualnych zasobów na końcówce /stats (MCOD-1208)


## 1.4.1 - (2019-02-20)
---

### New
* Wersjonowanie API
* Wprowadzenie wersji 1.4 API (niektóre widoki)
* Wyszukiwarka dla danych tabelarycznych 
* Indywidualne API dla każadego zasobu tabelarycznego 
* Mechanizm tłumaczeń na bazie danych
* Obsługa wyszukiwania przybliżonego (tzw. literówki)
* Obsługa wyszukiwania po fragmencie fraz 
* Obsługa wyszukiwania wyrazów bez polskich znaków 
* Tłumaczenie kategorii 
* Walidacja numerów telefonu i faxu w formularzach 
* Komunikaty techniczne 
* Obsługa sortowania zbiorów po popularności 
* Możliwość pobrania danych tabelarycznych w formacie JSON

### Changes
* Udoskonalony mechanizm indeksowania danych tabelarycznych
* Poprawki wydajnościowe w mechanizmie indeksowania danych tabelarycznych

### Fixes
* Błędne działanie filtrów wyszukiwarki :
    - IDS
    - CONTAINS
    - STARTSWITH
    - ENDSWITH
    - EXCLUDE
* Poprawka do sortowania alfaberycznego wyników wyszukiwania dla języka polskiego
* Bład typu 500 podczas wyświetlania dokumentacji 
* Poprawka dotycząca właściwego rozpoznawania typu skompresowanego XLSX 
* Poprawka do zunifikowanego mechanizmu logowania 
* Poprawka komunikatu o błedzie wyświetlanego podczas logowania 
* Różne poprawki związane z generowaniem raportów CSV 
* Dodanie wymagalności na polu "słowa kluczowe" 
* Dodanie ID użytkownika w raportach CSV 
* Dodawanie zasobu z linki 
* Obsługa nierozpoznanego kodowania znaków w pliku zasobu
