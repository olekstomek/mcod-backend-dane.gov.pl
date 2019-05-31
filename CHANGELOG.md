# CHANGELOG



## Unreleased
---

### New

### Changes

### Fixes

### Breaks


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
