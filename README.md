# KONFIGURACJA ŚRODOWISKA DEWELOPERSKIEGO

## Instalacja narzędzi docker oraz docker-compose.

Opis instalacji Dockera: https://docs.docker.com/install

Opis istalacji docker-compose: https://docs.docker.com/compose/install

## Instalacja systemu kontroli wersji Git.

Do zarządzania kodem źródłowym projektu używany jest system kontroli wersji Git.
Instrukcja instalacji systemu znajduje się pod adresem:
https://git-scm.com/book/en/v2/Getting-Started-Installing-Git

## Pobranie repozytoriów projektu: `backend`, `frontend`, `test-data`.

    $ git clone https://gitlab.dane.gov.pl/mcod/backend.git
    $ cd backend
    $ git clone https://gitlab.dane.gov.pl/mcod/frontend.git
    $ git clone https://gitlab.dane.gov.pl/mcod/test-data.git

## Uruchomienie kontenerów Docker.

Proces budowania środowiska może trwać nawet kilkadziesiąt minut w zależności od hosta.

    $ docker-compose up -d mcod-db
    $ docker-compose exec mcod-db dropdb mcod --username=mcod
    $ docker-compose exec mcod-db createdb mcod -O mcod --username=mcod
    $ docker-compose up -d mcod-db mcod-elasticsearch mcod-nginx mcod-rabbitmq mcod-rdfdb mcod-redis

W przypadku korzystania z IDE PyCharm (Professional) możliwe jest dodanie konfiguracji dotyczącej zarządzania kontenerami.

Więcej: https://www.jetbrains.com/help/pycharm/docker-compose.html#working

## Przygotowanie i uruchomienie wirtualnego środowiska

    $ python3 -m venv venv
    $ source venv/bin/activate
    (venv) $ pip install -r requirements-devel.txt

## Zaaplikowanie migracji i inicjalnych danych

    (venv) $ python manage.py init_mcod_db

## Utworzenie indeksów w ES

    (venv) $ python manage.py search_index --rebuild -f

## Rewalidacja zasobów

    (venv) $ python manage.py validate_resources --async

W przypadku użycia flagi `async` należy najpierw uruchomić Celery (instrukcja niżej), gdyż rewalidacja będzie odbywać się w ramach tasków Celery.

## Uruchomienie/zatrzymanie usług.

Aby uruchomić wszystkie usługi w katalogu projektu `backend` wykonaj:

    $ docker-compose up -d

Opcjonalnie można uruchamiać tylko wybrane usługi wyspecyfikowane jako parametr polecenia:

    $ docker-compose up -d mcod-db mcod-elasticsearch

Aby zatrzymać wybraną usługę, w katalogu projektu `backend` wykonaj:

    $ docker-compose stop mcod-elasticsearch

Aby zatrzymać usługę łącznie z usunięciem kontenera, w katalogu `backend` wykonaj:

    $ docker-compose down mcod-db

Aby zatrzymać usługę łącznie z usunięciem kontenera oraz powiązanych z nim wolumenów (całkowite usunięcie usługi), w katalogu `backend` wykonaj:

    $ docker-compose down -v mcod-db

## Ustawienia lokalne - przypisanie nazw maszyn do kontenera mcod-nginx.

Dodaj mapowanie adresu IP:

    Adres IP: 172.18.18.100

do nazw maszyn:

    mcod.local
    api.mcod.local
    admin.mcod.local
    cms.mcod.local

oraz dodaj mapowanie adresu IP:

    Adres IP: 172.18.18.23

do maszyny:

    mcod-rdfdb

## Ręcznie uruchamianie usług

Poza specyficznymi dla każdej usługi zmiennymi środowiskowymi, dla wszystkich usług należy ustawić zmienne środowiskowe:

    PYTHONUNBUFFERED=1;
    ENABLE_VAULT_HELPERS=no;
    ENVIRONMENT=local;
    NO_REPLY_EMAIL=env@test.local;
    ALLOWED_HOSTS=*;
    BASE_URL=http://mcod.local;
    API_URL=http://api.mcod.local;
    ADMIN_URL=http://admin.mcod.local;
    CMS_URL=http://cms.mcod.local;
    API_URL_INTERNAL=http://api.mcod.local;
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

    (venv) $ python manage.py runserver 0:8001

Po uruchomieniu usługi, pod adresem https://admin.mcod.local będzie dostępny panel administracyjny.
Możliwe jest zalogowanie się na konta 2 użytkowników:
* login: admin@mcod.local, hasło:testadmin123!
* login: pelnomocnik@mcod.local, hasło: User123!


### Usługa API (api.mcod.local)

    (venv) $ python -m werkzeug.serving --bind 0:8000 --reload --debug mcod.api:app

### Usługa CMS (cms.mcod.local)

#### Dodatkowe zmienne środowiskowe

    COMPONENT=cms;

#### Uruchamianie

    (venv) $ python manage.py runserver 0:8002

Po uruchomieniu usługi, będzie ona dostępna pod adresem https://cms.mcod.local/admin/


### Aplikacja WWW - frontend (mcod.local)

    $ docker-compose up -d mcod-frontend

Po uruchomieniu usługi, po upływie ok 1 minuty, pod adresem https://www.mcod.local bedzie dostępna aplikacja WWW - portal Otwarte Dane.

Do prawidłowego funkcjonowania niezbędne jest uruchomienie usługi API.

### Usługa celery

#### Dodatkowe zmienne środowiskowe

    COMPONENT=celery;

#### Uruchamianie

Uruchomienie usługi jest niezbędne, jeżeli zamierzamy korzystać z zadań asynchronicznych, takich jak wysyłanie maili czy walidacja plików zasobów.

    (venv) $ python -m celery --app=mcod.celeryapp:app worker -l DEBUG -E -Q default,resources,indexing,periodic,newsletter,notifications,search_history,watchers,harvester,indexing_data

## Inne przydatne polecenia.

### Uruchamianie testów jednostkowych

    (venv) $ tox

### Reindeksacja wszystkich danych

    (venv) $ python manage.py search_index --rebuild

### Ponowna walidacja zasobów o danych identyfikatorach <id_1,...,id_N>

    (venv) $ python manage.py validate_resources --where 'id in (<id_1,...,id_N>)'

### Ponowna walidacja zasobu o danym identyfikatorze <id>

    (venv) $ python manage.py validate_resources --where id=<id>

### Zaindeksowanie pliku zasobu (wygenerowanie danych tabelarycznych)

    (venv) $ python manage.py index_file --pks <id_1,...,id_N>
