# KONFIGURACJA ŚRODOWISKA DEWELOPERSKIEGO

## Instalacja narzędzi docker oraz docker-compose

Opis instalacji Docker'a: https://docs.docker.com/install

Opis instalacji docker-compose: https://docs.docker.com/compose/install

## Instalacja systemu kontroli wersji Git

Do zarządzania kodem źródłowym projektu używany jest system kontroli wersji Git.
Instrukcja instalacji systemu znajduje się pod adresem:
https://git-scm.com/book/en/v2/Getting-Started-Installing-Git

## Pobranie repozytorium projektu

```
$ git clone https://gitlab.dane.gov.pl/mcod/backend.git
$ cd backend
```

## Uruchomienie środowiska — część wspólna

Lokalne środowisko można uruchomić na dwa sposoby:

- w docker compose
- na swoim hoście

Obie opcje dockeryzują zależności, takie jak baza danych i obie wymagają konfiguracji wspólnej opisanej w następnej
sekcji.

### Konfiguracja zmiennych środowiskowych

Aby projekt działał prawidłowo, należy skopiować zawartość pliku `env.sample` do nowo utworzonego pliku `.env`.

#### Informacja o FIELD_ENCRYPTION_KEYS

Do poprawnego działania biblioteki `django-searchable-encrypted-fields` należy wygenerować klucz szyfrowania
(`encryption key`) za pomocą biblioteki `secrets`, np.:

```shell
python -c "import secrets; print(secrets.token_hex(32))"
```

Klucz ten jest niezbędny, ponieważ biblioteka szyfruje i odszyfrowuje dane zapisane w bazie – działa w obie strony.
Wygenerowany klucz należy przypisać do zmiennej `FIELD_ENCRYPTION_KEYS` w pliku `.env`.

Zmiennej tej należy przypisać listę kluczy, oddzielonych przecinkami. Nowe klucze dodaje się na początku listy (czyli
przed starymi).
Więcej
informacji [na stronie projektu](https://pypi.org/project/django-searchable-encrypted-fields/).

**Przykład:**

```
FIELD_ENCRYPTION_KEYS=new_key,previous_key
```

#### Konfiguracja wysyłki maili

Środowisko lokalne oferuje dwie opcje:

- `filebased`, czyli zapis maili do pliku w `/tmp`,
- `smtp`, czyli użycie [mailhog](https://hub.docker.com/r/mailhog/mailhog).

Środowisko domyślnie używa wersji z SMTP, żeby zobaczyć wysłane maile, wejdź na https://mail.mcod.local (proxy do
serwisu `mcod-smtp`).
Żeby to zmienić, wyedytuj plik `local.py` lub usuń zmienną środowiskową `EMAIL_HOST`.
Testy używają opcji `filebased`.

### Konfiguracja Django

Aby projekt działał prawidłowo, należy skopiować zawartość pliku `mcod/settings/local.py.sample` do nowo utworzonego
pliku `mcod/settings/local.py`.
Konfiguracja Django realizowana jest na podstawie ustawień z pliku `mcod/settings/base.py`, które są nadpisywane
ustawieniem z pliku `mcod/settings/local.py`.

### Struktura konfiguracji

Zmienne konfiguracyjne idą w tej kolejności:

1. `.env` jest źródłem zmiennych środowiskowych
   - dla docker-compose'a (zmienne w plikach docker-compose\*.yml)
   - dla aplikacji za pośrednictwem `base.py`
2. aplikacja samodzielnie czyta zmienne środowiskowe w `base.py`
3. `local.py`, `test.py` importują wszystko z `base.py`

Co oznacza, że plik `.env` nadpisuje zmienne środowiskowe, jeśli jest dostępny dla aplikacji.
Z tego powodu i dla przejrzystości lokalne serwisy w docker-compose.local.yml używają `environment` zamiast `env_file`

### Utworzenie użytkownika w bazie danych

```shell
docker compose up -d mcod-db
```

Postgres przy pierwszym uruchomieniu [utworzy](https://hub.docker.com/_/postgres#postgres_user) bazę `mcod` i
użytkownika `mcod` z takim samym hasłem, zgodnie ze zmiennymi
środowiskowymi `POSTGRES_*`.

W przypadku korzystania z IDE PyCharm (Professional) możliwe jest dodanie konfiguracji dotyczącej zarządzania
kontenerami. Więcej informacji pod [linkiem](https://www.jetbrains.com/help/pycharm/docker-compose.html#working).

Wybrany kontener uruchamia `python manage.py` w środowisku docker-compose'a, wraz z zależnościami.

### Przypisanie nazw maszyn do kontenera mcod-nginx

Wyedytuj plik `/etc/hosts`, tak by nazwy serwisów mcod rozwiązywały się na adres IP usługi `mcod-nginx` (patrz
`docker-compose.yml`).

```text
172.18.18.100       mcod.local api.mcod.local admin.mcod.local cms.mcod.local forum.mcod.local mail.mcod.local
```

**Uwaga dla MacOS**: zamień adres `172.18.18.100` na `127.0.0.1`.
Docker na MacOS nie działa natywnie i adresy wewnętrzne z sieci dockerowych nie są osiągalne z poziomu hosta.

## Uruchomienie środowiska lokalnego w docker-compose

🚧 Proces budowania środowiska może trwać nawet kilkadziesiąt minut w zależności od Twojego komputera, sieci itp.

W procesie tym osiągniesz następujące cele:

1. działające zależności, takie jak baza danych
2. możliwość uruchomienia testów lokalnie
3. możliwość zalogowania się do Panelu Administracyjnego
4. działający CMS Wagtail
5. działające kolejki Celery
6. zaślepioną wysyłkę maili

### Zbudowanie kontenerów

W związku z mirrorowaniem obrazu discource, przed wykonaniem poniższej komendy, trzeba się zalogować do gitlaba.
Wejdź na [stronę rejestru](https://gitlab.dane.gov.pl/mcod/backend/container_registry), rozwiń "CLI Commands" i wykonaj
komendę rozpoczynającą się od
`docker login`. Alternatywnie — wyłącz kontenery discourse i przestaw zmienną `DISCOURSE_FORUM_ENABLED` na `false`.

```shell
docker compose -f docker-compose.local.yml build
```

### Załadowanie inicjalnych danych

```shell
docker compose -f docker-compose.local.yml run mcod-local-run python manage.py init_mcod_db
```

Uwaga: zadanie do wykonania jednorazowo, również dla środowiska bare-metal, dane są zapisane w wolumenie mcod-db.

### Utworzenie indeksów w ES

```shell
docker compose up mcod-db mcod-elasticsearch
docker compose -f docker-compose.local.yml run mcod-local-run python manage.py
```

Uwaga: zadanie do wykonania jednorazowo, również dla środowiska bare-metal, dane są zapisane w wolumenie
mcod-elasticsearch.

### Konfiguracja nginx

Nginx wymaga zmiennych środowiskowych MCOD_NGINX\_\* wskazujących na usługi w dockerze.
Ustaw je w `.env`:

```dotenv
MCOD_NGINX_WS=http://172.18.18.104:8001
MCOD_NGINX_PN_APPS=http://172.18.18.101:8001
MCOD_NGINX_API=http://172.18.18.102:8000
MCOD_NGINX_ADMIN=http://172.18.18.101:8001
MCOD_NGINX_CMS=http://172.18.18.103:8002
```

Adresy odpowiadają adresom usług w `docker-compose.local.yml`.

### Uruchomienie usług

```shell
docker compose -f docker-compose.local.yml up
```

Lub wybranych:

```shell
docker compose -f docker-compose.local.yml up mcod-local-admin mcod-local-cms
```

Aby uruchomić shell w kontenerze:

```shell
docker compose -f docker-compose.local.yml run --entrypoint bash mcod-local-celery
```

#### Celery — Taski periodyczne

Aby uruchomić [celery beat](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#introduction)
wyedytuj zmienne środowiskowe serwisu `mcod-local-celery` w pliku `docker-compose.local.yml`.
Odkomentuj odpowiednią wartość `CELERY_OPTS`:

```yaml
# no scheduler
CELERY_OPTS: "-l DEBUG"
# using beat
# CELERY_OPTS: "-l DEBUG -B --scheduler django_celery_beat.schedulers:DatabaseScheduler"
```

### Sprawdzenie statusu — zdrowie kontenerów

Czy są kontenery, które wyszły z `exit status != 0`?

```shell
docker compose -f docker-compose.local.yml ps --all
```

Jeśli są — sprawdź ich logi.

### Sprawdzenie statusu — Panel Administracyjny

Po uruchomieniu usługi `mcod-local-admin`, pod adresem https://admin.mcod.local będzie dostępny panel administracyjny.
Możliwe jest zalogowanie się na konta 2 użytkowników:

- login: admin@mcod.local, hasło:testadmin123!
- login: pelnomocnik@mcod.local, hasło: User123!

### Sprawdzenie statusu — połączenia między kontenerami

Na potrzeby np. harvestacji celery musi móc się połączyć do api.
Kontener celery wykonuje setup certyfikatów w entrypoint'cie.

Poprawne zachowanie to 200:

```shell
❯ docker compose -f docker-compose.local.yml -f docker-compose.override.yml run --entrypoint bash mcod-local-celery
root@2f1ba9b58144:/usr/src/mcod_backend# /usr/local/bin/start-celery-local
Installing local SSL certificates for Celery->API communication
2025-10-07 12:07:24,475 mcod         DEBUG    Started configuring certifi..
2025-10-07 12:07:24,477 mcod         INFO     Certi file updated successfully.
wait-for-it: waiting 30 seconds for mcod-rabbitmq:5672
wait-for-it: mcod-rabbitmq:5672 is available after 0 seconds
^C
Aborted!
root@2f1ba9b58144:/usr/src/mcod_backend# python -c 'import requests; print(requests.get("https://cms.mcod.local"))'
<Response [502]>
root@2f1ba9b58144:/usr/src/mcod_backend#
```

W razie problemów z certyfikatem dostaniemy taki błąd:

```shell
❯ docker compose -f docker-compose.local.yml -f docker-compose.override.yml run --entrypoint bash mcod-local-celery
[+] Creating 1/1
 ✔ Container mcod-nginx  Running                                                                                                                                                                           0.0s
root@5878a8087580:/usr/src/mcod_backend# python -c 'import requests; print(requests.get("https://cms.mcod.local"))'
Traceback (most recent call last):
………
requests.exceptions.SSLError: HTTPSConnectionPool(host='cms.mcod.local', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate (_ssl.c:1131)')))
```

Powyższy przykład działa, ponieważ użyliśmy `bash` jako entrypoint.

#### Naprawa ad hoc

```shell
❯ docker compose -f docker-compose.local.yml run --entrypoint bash mcod-local-celery
root@5878a8087580:/usr/src/mcod_backend# python manage.py configure_nginx_certs /usr/src/mcod_backend/mcod.local.pem
2025-09-19 09:35:59,353 mcod         DEBUG    Started configuring certifi..
2025-09-19 09:35:59,363 mcod         INFO     Certi file updated successfully.
```

#### Co sprawdzić, jak nie działa

- czy jest podmontowany volume z certyfikatami
  `./docker/nginx/certs/mcod.local.pem:/usr/src/mcod_backend/mcod.local.pem`
- czy ścieżki w pliku [start-celery-local.sh](docker/app/start-celery-local.sh) zgadzają się z w/w wolumenem
- czy `mcod-nginx` używa tych samych certyfikatów

### Sprawdzenie statusu — API

```shell
docker compose -f docker-compose.local.yml up mcod-local-api
```

API jest dostępne pod [api.mcod.local](https://api.mcod.local), dokumentacja
OpenApi: [/doc](https://api.mcod.local/doc?urls.primaryName=DANE.GOV.PL%20API%20v1.4).

### Sprawdzenie statusu — Celery

Do sprawdzenia stanu Celery najlepiej użyć [Flower](https://flower.readthedocs.io/en/latest/). Jest to opcjonalny
komponent, więc trzeba uruchomić go osobno:

GUI będzie dostępne na porcie 8888, [link](http://localhost:8888/).

Celery działa, jeśli na liście workerów na pierwszej stronie widać jeden o nazwie zaczynającej się od `celery@`.

### Sprawdzenie statusu — CMS

```shell
docker compose -f docker-compose.local.yml up mcod-local-cms
```

Wagtail jest dostępny pod [cms.mcod.local](https://cms.mcod.local/admin). Dane do logowania są te same co dla Panelu
Administracyjnego.
CMS działa, jeśli da się zalogować, dalsza konfiguracja jest poza zakresem tego punktu.

### Usługa Discourse

Discourse jest dostępny pod [forum.mcod.local](https://forum.mcod.local). Po wykonaniu konfiguracji powinien być
widoczny jeden wątek "Welcome to Discourse".

#### Pierwsza konfiguracja

Komenda umożliwia skonfigurowanie instancji forum Discourse – od wygenerowania systemowego klucza API, przez ustawienia,
aż po instalację motywu i synchronizację użytkowników.

Uwaga: username i password muszą się zgadzać z .env.

```shell
docker compose -f docker-compose.local.yml up -d mcod-local-admin mcod-nginx mcod-discourse
docker compose -f docker-compose.local.yml run mcod-local-run \
  python manage.py set_up_forum \
  --file data/discourse/settings.json \
  --theme_path data/discourse/discourse-otwarte-dane-theme.zip \
  --username user \
  --password bitnami123
```

#### Ustawienie API_KEY

Po wykonaniu powyższej komendy utworzy się plik `mcod/api_key.txt`. Zawartość pliku należy przekopiować i wkleić do
zmiennej `DISCOURSE_API_KEY` w pliku `.env`

### Uruchomienie testów

Testy działają, jeśli da się uruchomić pojedynczy test. Działający przykład:

```shell
docker compose -f docker-compose.local.yml run mcod-local-tests -n1 mcod/resources/tests/test_admin/test_file_validation.py
```

### Zdalne debugowanie

PyCharm może używać interpretera Python zainstalowanego w kontenerze w serwisie w docker compose.
Więcej
informacji [w dokumentacji](https://www.jetbrains.com/help/pycharm/using-docker-compose-as-a-remote-interpreter.html#debug-django-application).

- podczas konfiguracji wskaż oba pliki: `docker-compose.yml` i `docker-compose.local.yml`
- wybierz serwis, który nie rezerwuje adresu IP ani portu, ani nie ma ustawionego entrypointa, np. `mcod-local-run`
  Pozwala to uruchomić np. celery pod debugerem wbudowanym w IDE.

## Uruchomienie środowiska bare metal

### Uruchomienie/zatrzymanie usług (zależności)

Aby uruchomić wszystkie usługi w katalogu projektu `backend` wykonaj:

```
$ docker compose up
```

Opcjonalnie można uruchamiać tylko wybrane usługi wyspecyfikowane jako parametr polecenia:

```
$ docker compose up -d mcod-db mcod-elasticsearch
```

Aby zatrzymać wybraną usługę, w katalogu projektu `backend` wykonaj:

```
$ docker compose stop mcod-elasticsearch
```

Aby zatrzymać usługę łącznie z usunięciem kontenera, w katalogu `backend` wykonaj:

```
$ docker compose down mcod-db
```

Aby zatrzymać usługę łącznie z usunięciem kontenera oraz powiązanych z nim wolumenów (całkowite usunięcie usługi), w
katalogu `backend` wykonaj:

```
$ docker compose down -v mcod-db
```

### Konfiguracja nginx

Nginx wymaga zmiennych środowiskowych MCOD_NGINX\_\* wskazujących na usługi w dockerze.
Ustaw je w `.env`:

```dotenv
MCOD_NGINX_WS=http://host.docker.internal:8001
MCOD_NGINX_PN_APPS=http://host.docker.internal:8001
MCOD_NGINX_API=http://host.docker.internal:8000
MCOD_NGINX_ADMIN=http://host.docker.internal:8001
MCOD_NGINX_CMS=http://host.docker.internal:8002
```

Ta konfiguracja oznacza, że nginx będzie proxował ruch na hosta.

### Konfiguracja smtp

Środowisko bare metal może używać mailhoga, ale należy ustawić zmienną środowiskową w .env:

```dotenv
EMAIL_HOST=localhost
```

### Przygotowanie i uruchomienie wirtualnego środowiska

```
$ pip install -I pipenv==2022.10.12
$ pipenv run pip install setuptools"<58"
$ pipenv install
$ exit
$ pipenv shell
```

### Zaaplikowanie migracji i inicjalnych danych

```
(backend) $ python manage.py init_mcod_db
```

Uwaga: zadanie do wykonania jednorazowo, również dla środowiska docker, dane są zapisane w wolumenie mcod-db.

### Utworzenie indeksów w ES

```
(backend) $ python manage.py search_index --rebuild -f
```

Uwaga: zadanie do wykonania jednorazowo, również dla środowiska docker, dane są zapisane w wolumenie mcod-elasticsearch.

## Ustawienia lokalne - logowanie przez Węzeł Krajowy (logingovpl)

Pomocnicza zmienna środowiskowa `USERS_TEST_LOGINGOVPL` (`False`/`True`) umożliwia wyłączenie komunikacji z Węzłem Krajowym, poprzez wykorzystanie lokalnego formularza logowania, imitującego ten zwracany z Węzła Krajowego.

## Ustawienia certyfikatów mcod-nginx.

Aby biblioteka certifi poprawnie używała certyfikatów nginx, należy dodać odpowiedni wpis do pliku cacert.pem.
Aby to zrobić, należy uruchomić komendę:

```
(backend) $ python manage.py configure_nginx_certs ./docker/nginx/certs/mcod.local.pem
```

Jest to konieczne, by lokalny harvester nie rzucał błędami związanymi z SSL.

### Ręcznie uruchamianie usług

Poza specyficznymi dla każdej usługi zmiennymi środowiskowymi, dla wszystkich usług należy ustawić zmienne środowiskowe:

```
PYTHONUNBUFFERED=1;
ENVIRONMENT=local;
NO_REPLY_EMAIL=env@test.local;
ALLOWED_HOSTS=*;
BASE_URL=https://mcod.local;
API_URL=https://api.mcod.local;
ADMIN_URL=https://admin.mcod.local;
CMS_URL=https://cms.mcod.local;
API_URL_INTERNAL=https://api.mcod.local;
DEBUG=yes;
```

#### Usługa Admin Panel (admin.mcod.local)

##### Dodatkowe zmienne środowiskowe

```dotenv
COMPONENT=admin;
```

##### Uruchamianie

```
(backend) $ python manage.py runserver 0:8001
```

#### Usługa API (api.mcod.local)

```
(backend) $ python -m werkzeug.serving --bind 0:8000 --reload --debug mcod.api:app
```

#### Usługa CMS (cms.mcod.local)

##### Dodatkowe zmienne środowiskowe

```
COMPONENT=cms;
```

##### Uruchamianie

```
(backend) $ python manage.py runserver 0:8002
```

Po uruchomieniu usługi będzie ona dostępna pod adresem https://cms.mcod.local/admin/

#### Aplikacja WWW - frontend (mcod.local)

Instrukcja uruchomienia frontend w pliku `frontend/README.md`

Do prawidłowego funkcjonowania niezbędne jest uruchomienie usługi API.

#### Usługa Celery

##### Dodatkowe zmienne środowiskowe

```
COMPONENT=celery;
```

##### Uruchamianie

Uruchomienie usługi jest niezbędne, jeżeli zamierzamy korzystać z zadań asynchronicznych, takich jak wysyłanie maili czy
walidacja plików zasobów.

```
(backend) $ python -m celery --app=mcod.celeryapp:app worker -l DEBUG -E -Q default,resources,indexing,periodic,newsletter,notifications,search_history,watchers,harvester,indexing_data,history,graphs,datasets,archiving,reports,discourse,showcases
```

###### Taski periodyczne

Aby uruchomić [celery beat](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#introduction) dodaj flagę
`-B` do powyższego polecenia.

#### Usługa Discourse

Discourse jest dostępny pod [forum.mcod.local](https://forum.mcod.local).

##### Pierwsza konfiguracja

Komenda umożliwia skonfigurowanie instancji forum Discourse – od wygenerowania systemowego klucza API, przez ustawienia,
aż po instalację motywu i synchronizację użytkowników.

```
(backend) python manage.py set_up_forum --file data/discourse/settings.json --theme_path data/discourse/discourse-otwarte-dane-theme.zip --username user --password bitnami123
```

##### Ustawienie API_KEY

Po wykonaniu powyższej komendy utworzy się plik `mcod/api_key.txt`. Zawartość pliku należy przekopiować i wkleić do
zmiennej `DISCOURSE_API_KEY` w pliku `.env`

## Dalsza konfiguracja środowiska

Sekcja zawiera kolejne, opcjonalne elementy setupu, do wykonania po pierwszym uruchomieniu.

### Zmiana harmonogramu tasków periodycznych

Taski periodyczne są uruchamiane zgodnie z harmonogramem określonym w kodzie, w zmiennej `beat_schedule`. Można jednak
zmienić domyślny harmonogram startu dla tasków periodycznych poprzez ustawienie zmiennej środowiskowej
UPDATE_TASKS_CELERY_BEAT_TIME.

Na przykład — zmiana czasu startu 2 tasków periodycznych:

```
  UPDATE_TASKS_CELERY_BEAT_TIME='{"kronika_sparql_performance": {"day_of_month":2, "hour": 23, "minute": 20}, "catalog_xml_file_creation":{"hour": 7, "minute": 15}}'
```

Tworzenie wykazu głównego: dla zadania realizującego tworzenie wykazu głównego DGA niezbędne jest ustawienie zmiennej
środowiskowej określającej id Instytucji będącej jego właścicielem:

```
  MAIN_DGA_DATASET_OWNER_ORGANIZATION_PK=\<organization_pk>
```

Tworzenie raportu `katalog.xml` przez task `create_xml_metadata_files` może zostać dezaktywowane przez ustawienie
zmiennej środowiskowej

```
  ENABLE_CREATE_XML_METADATA_REPORT=False
```

## Inne przydatne polecenia

Przykłady komend `manage.py` poniżej są minimalne; by uruchomić je w dockerze trzeba użyć:

```shell
docker compose -f docker-compose.local.yml run mcod-local-run python manage.py TUTAJ_KOMENDA
```

### Kompilacja tłumaczeń (lokalnie)

Po zmianie tłumaczeń w pliku `translations/system/pl/LC_MESSAGES/django.po` należy przejść do katalogu
projektu,
w którym znajduje się plik `manage.py`. Następnie uruchomić polecenie:

```
(backend) $ python manage.py compilemessages
```

### Dodawanie nowych pakietów (Pipenv)

Standardowe dodanie nowej zależności (np. poprzez edycję `Pipfile` i uruchomienie instalacji) może spowodować niezamierzoną aktualizację wszystkich pozostałych pakietów w projekcie (`Pipfile.lock`).
Taka operacja niesie ryzyko wystąpienia błędów regresji i awarii testów, jeśli wersje innych bibliotek ulegną zmianie.

Aby dodać nowy pakiet, zachowując stabilne wersje pozostałych zależności, należy skorzystać z flagi `--keep-outdated`.

**Zalecana komenda:**

```bash
pipenv install django-csp=="3.7" --keep-outdated
```

Parametr `--keep-outdated` wymusza na Pipenv zaktualizowanie pliku Pipfile.lock wyłącznie dla nowo dodawanego pakietu, pozostawiając resztę zależności w ich dotychczasowych wersjach.
Zapewnia to spójność środowiska deweloperskiego i produkcyjnego.

### Uruchamianie testów jednostkowych

```
(backend) $ pytest
```

#### Testy w dockerze

`docker-compose.local.yml` zawiera konfigurację pozwalającą uruchomić testy w odizolowanym środowisku Dockerowym, z
podmontowanym kodem.
Warto sprawdzić testy w ten sposób szczególnie przy okazji dodawania zależności, również systemowych (takich jak np.
xmlsec). Jest to niezależne od tego, czy uruchamiasz resztę środowiska za pomocą dockera czy w opcji bare metal.

Uruchomienie wszystkich testów (analogicznie do wywołania `pytest`):

```shell
docker compose -f docker-compose.local.yml run mcod-local-tests
```

Lub z argumentami:

```shell
docker compose -f docker-compose.local.yml run mcod-local-tests mcod/guides/tests/test_api.py --no-cov
```

### Re-indeksacja wszystkich danych (DB->ES)

```
(backend) $ python manage.py search_index --rebuild
```

#### Dla wybranego modelu

```shell
(backend) $ python manage.py search_index --rebuild --models resources.Resource
```

### Ponowna walidacja zasobów o danych identyfikatorach \<id_1,..., id_N>

```
(backend) $ python manage.py validate_resources --where 'id in (<id_1,...,id_N>)'
```

### Ponowna walidacja zasobu o danym identyfikatorze <id>

```
(backend) $ python manage.py validate_resources --where id=<id>
```

### Zaindeksowanie pliku zasobu (wygenerowanie danych tabelarycznych)

```
(backend) $ python manage.py index_file --pks <id_1,...,id_N>
```

### Rewalidacja zasobów

```
(backend) $ python manage.py validate_resources --async
```

W przypadku użycia flagi `async` należy najpierw uruchomić Celery (instrukcja niżej), gdyż rewalidacja będzie odbywać
się w ramach tasków Celery.

### Uruchomienie narzędzia pre-commit (lokalnie)

Aby `pre-commit` uruchamiał się przy każdym commicie, trzeba go zainstalować:

```
(backend) pre-commit install
```

Dodanie pliku/plików jest niezbędne do sprawdzenia ich poprawności:

```
$ git add <filename>
```

Uruchomienie pre-commit sprawdzającego m.in. poprawność stylu i importów.

```
(backend) $ pre-commit run
```

#### Black

Używamy [black](https://black.readthedocs.io/en/stable/index.html) do zachowania stylu kodu.
Konfiguracja jest obecna tylko w `.pre-commit-config.yaml`, ponieważ nie używamy `pyproject.toml`.

`git blame` może ignorować commit z masowym reformatowaniem kodu, zobacz opcję
`--ignore-revs-file .git-blame-ignore-revs`

### Uruchamianie rozszerzonej konsoli Django - shell_plus ze wskazanym plikiem konfiguracyjnym

#### z domyślnym plikiem konfiguracyjnym - mcod/settings/base.py

```
(backend) python manage.py shell_plus
```

#### z innym wskazanym plikiem konfiguracyjnym - np. mcod/settings/test.py

```
(backend) python manage.py shell_plus --settings mcod.settings.test
```

### Synchronizacja użytkowników w Discourse

Każdy użytkownik o roli Administrator lub Pełnomocnik, podczas **dodawania, usuwania i edycji** w Admin Panelu jest
automatycznie synchronizowany z bazą forum
Discourse, a jego status zostaje zaktualizowany.
Podobnie przy **wylogowaniu** – użytkownik jest również wylogowywany z forum.
Istnieje alternatywna komenda, która synchronizuje użytkowników między serwisem **Otwarte Dane** a forum **Discourse**,
tworząc w bazie forum nowych użytkowników o statusie pełnomocnika lub administratora oraz zapisując ich klucz API w
bazie OD.

```
(backend) python manage.py set_up_forum --step_name sync_users
```

### Resetowanie django axes w przypadku lokalnego zablokowania konta.

Jeżeli pojawia się komunikat z settings.AXES_FAIL_MESSAGE (Too many failed login attempts..) użyj tej komendy.

```cmd
python manage.py axes_reset
```
