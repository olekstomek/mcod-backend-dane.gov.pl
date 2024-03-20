# KONFIGURACJA ŚRODOWISKA DEWELOPERSKIEGO

## Instalacja narzędzi docker oraz docker-compose.

Opis instalacji Docker'a: https://docs.docker.com/install

Opis instalacji docker-compose: https://docs.docker.com/compose/install

## Instalacja systemu kontroli wersji Git.

Do zarządzania kodem źródłowym projektu używany jest system kontroli wersji Git.
Instrukcja instalacji systemu znajduje się pod adresem:
https://git-scm.com/book/en/v2/Getting-Started-Installing-Git

## Pobranie repozytoriów projektu: `backend`, `frontend`, `test-data`.

    $ git clone https://gitlab.dane.gov.pl/mcod/backend.git
    $ cd backend
    $ git clone https://gitlab.dane.gov.pl/mcod/frontend.git
    $ git clone https://gitlab.dane.gov.pl/mcod/test-data.git

## Konfiguracja zmiennych środowiskowych:

Aby projekt działał prawidłowo, należy skopiować zawartość pliku env.sample do nowo utworzonego pliku .env.

## Konfiguracja Django:

Aby projekt działał prawidłowo, należy skopiować zawartość pliku `mcod/settings/local.py.sample` do nowo utworzonego pliku `mcod/settings/local.py`.
Konfiguracja Django realizowana jest na podstawie ustawień z pliku `mcod/settings/base.py`, które są nadpisywane ustawieniem z pliku `mcod/settings/local.py`.

## Uruchomienie kontenerów Docker.

Proces budowania środowiska może trwać nawet kilkadziesiąt minut w zależności od hosta.

    $ docker compose up -d mcod-db
    $ docker compose exec mcod-db dropdb mcod --username=mcod
    $ docker compose exec mcod-db createdb mcod -O mcod --username=mcod
    $ docker compose up -d mcod-db mcod-elasticsearch mcod-nginx mcod-rabbitmq mcod-rdfdb mcod-redis

**Uwaga:** Aby kontenery uruchomiły się poprawnie, należy dodać zmienną środowiskową do pliku .env: PWD określającą ścieżkę absolutną do projektu.

W przypadku korzystania z IDE PyCharm (Professional) możliwe jest dodanie konfiguracji dotyczącej zarządzania kontenerami.

Więcej: https://www.jetbrains.com/help/pycharm/docker-compose.html#working

## Przygotowanie i uruchomienie wirtualnego środowiska

    $ pip install -I pipenv
    $ pipenv run pip install setuptools"<58"
    $ pipenv install --dev
    $ exit
    $ pipenv shell

## Zaaplikowanie migracji i inicjalnych danych

    (backend) $ python manage.py init_mcod_db

## Utworzenie indeksów w ES

    (backend) $ python manage.py search_index --rebuild -f

## Rewalidacja zasobów

    (backend) $ python manage.py validate_resources --async

W przypadku użycia flagi `async` należy najpierw uruchomić Celery (instrukcja niżej), gdyż rewalidacja będzie odbywać się w ramach tasków Celery.

## Uruchomienie/zatrzymanie usług.

Aby uruchomić wszystkie usługi w katalogu projektu `backend` wykonaj:

    $ docker compose up -d

Opcjonalnie można uruchamiać tylko wybrane usługi wyspecyfikowane jako parametr polecenia:

    $ docker compose up -d mcod-db mcod-elasticsearch

Aby zatrzymać wybraną usługę, w katalogu projektu `backend` wykonaj:

    $ docker compose stop mcod-elasticsearch

Aby zatrzymać usługę łącznie z usunięciem kontenera, w katalogu `backend` wykonaj:

    $ docker compose down mcod-db

Aby zatrzymać usługę łącznie z usunięciem kontenera oraz powiązanych z nim wolumenów (całkowite usunięcie usługi), w katalogu `backend` wykonaj:

    $ docker compose down -v mcod-db

## Ustawienia lokalne - przypisanie nazw maszyn do kontenera mcod-nginx.

Dodaj mapowanie adresu IP:

    Adres IP: 172.18.18.100

Do nazw maszyn:

    mcod.local
    api.mcod.local
    admin.mcod.local
    cms.mcod.local

Oraz dodaj mapowanie adresu IP:

    Adres IP: 172.18.18.23

Do maszyny:

    mcod-rdfdb

## Ustawienia certyfikatów mcod-nginx.

Aby biblioteka certifi poprawnie używała certyfikatów nginx, należy dodać odpowiedni wpis do pliku cacert.pem.
Aby to zrobić, należy uruchomić komendę:

    (backend) $ python manage.py configure_nginx_certs


## Ręcznie uruchamianie usług

Poza specyficznymi dla każdej usługi zmiennymi środowiskowymi, dla wszystkich usług należy ustawić zmienne środowiskowe:

    PYTHONUNBUFFERED=1;
    ENABLE_VAULT_HELPERS=no;
    ENVIRONMENT=local;
    NO_REPLY_EMAIL=env@test.local;
    ALLOWED_HOSTS=*;
    BASE_URL=https://mcod.local;
    API_URL=https://api.mcod.local;
    ADMIN_URL=https://admin.mcod.local;
    CMS_URL=https://cms.mcod.local;
    API_URL_INTERNAL=https://api.mcod.local;
    DEBUG=yes;

### Panel administracyjny (admin.mcod.local)

#### Dodatkowe zmienne środowiskowe

    COMPONENT=admin;
    BOKEH_DEV=True;
    BOKEH_RESOURCES=cdn;
    BOKEH_ALLOW_WS_ORIGIN=mcod.local;
    BOKEH_LOG_LEVEL=debug;
    BOKEH_PY_LOG_LEVEL=debug;
    BOKEH_MINIFIED=False;
    BOKEH_VALIDATE_DOC=False;
    BOKEH_PRETTY=True;
    STATS_LOG_LEVEL=DEBUG;
    DJANGO_ADMINS=Jon Doe:jond@test.com,Jane Smith:jane.smith@example.com.pl;
    DATASET_ARCHIVE_FILES_TASK_DELAY=1;

#### Uruchamianie

    (backend) $ python manage.py runserver 0:8001

Po uruchomieniu usługi, pod adresem https://admin.mcod.local będzie dostępny panel administracyjny.
Możliwe jest zalogowanie się na konta 2 użytkowników:
* login: admin@mcod.local, hasło:testadmin123!
* login: pelnomocnik@mcod.local, hasło: User123!


### Usługa API (api.mcod.local)

    (backend) $ python -m werkzeug.serving --bind 0:8000 --reload --debug mcod.api:app

### Usługa CMS (cms.mcod.local)

#### Dodatkowe zmienne środowiskowe

    COMPONENT=cms;

#### Uruchamianie

    (backend) $ python manage.py runserver 0:8002

Po uruchomieniu usługi będzie ona dostępna pod adresem https://cms.mcod.local/admin/


### Aplikacja WWW - frontend (mcod.local)

Instrukcja uruchomienia frontend w pliku `frontend/README.md`

Do prawidłowego funkcjonowania niezbędne jest uruchomienie usługi API.

### Usługa celery

#### Dodatkowe zmienne środowiskowe

    COMPONENT=celery;

#### Uruchamianie

Uruchomienie usługi jest niezbędne, jeżeli zamierzamy korzystać z zadań asynchronicznych, takich jak wysyłanie maili czy walidacja plików zasobów.

    (backend) $ python -m celery --app=mcod.celeryapp:app worker -l DEBUG -E -Q default,resources,indexing,periodic,newsletter,notifications,search_history,watchers,harvester,indexing_data

### Usługa discourse

#### Pierwsza konfiguracja

    (backend) python manage.py set_up_forum --file /.../backend/data/discourse/settings.json --theme_path /.../backend/data/discourse/discourse-otwarte-dane-theme.zip --password bitnami123 --username user

#### Ustawienie API_KEY

Po wykonaniu powyższej komendy utworzy się plik api_key.txt w folderze mcod/. Zawartość pliku należy przekopiować i wkleić do zmiennej DISCOURSE_API_KEY w pliku .env

#### Kolejna konfiguracja

Pierwsza konfiguracja nie wykonała poprawnie kroku sync_user, bo brakowało utworzonego klucza API_KEY, stąd trzeba wykonać ten krok ponownie.


    (backend) python manage.py set_up_forum --step_name sync_users


## Inne przydatne polecenia.

### Uruchamianie testów jednostkowych

    (backend) $ tox

### Re-indeksacja wszystkich danych

    (backend) $ python manage.py search_index --rebuild

### Ponowna walidacja zasobów o danych identyfikatorach <id_1,..., id_N>

    (backend) $ python manage.py validate_resources --where 'id in (<id_1,...,id_N>)'

### Ponowna walidacja zasobu o danym identyfikatorze <id>

    (backend) $ python manage.py validate_resources --where id=<id>

### Zaindeksowanie pliku zasobu (wygenerowanie danych tabelarycznych)

    (backend) $ python manage.py index_file --pks <id_1,...,id_N>

### Uruchomienie narzędzia pre-commit (lokalnie)

Aby `pre-commit` uruchamiał się przy każdym commicie, trzeba go zainstalować:

    (backend) pre-commit install

Dodanie pliku/plików jest niezbędne do sprawdzenia ich poprawności:

    $ git add <filename>

Uruchomienie pre-commit sprawdzającego m.in. poprawność stylu i importów.

    (backend) $ pre-commit run
