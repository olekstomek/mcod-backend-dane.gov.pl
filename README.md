#KONFIGURACJA ŚRODOWISKA DEWELOPERSKIEGO

##Instalacja narzędzi docker oraz docker-compose.

Opis instalacji Dockera: https://docs.docker.com/install

Opis istalacji docker-compose: https://docs.docker.com/compose/install

##Instalacja systemu kontroli wersji Git.

Do zarządzania kodem źródłowym projektu używany jest system kontroli wersji Git.
Instrukcja instalacji systemu znajduje się pod adresem:
https://git-scm.com/book/en/v2/Getting-Started-Installing-Git

##Pobranie repozytoriów projektu: `backend`, `frontend`, `test-data`.

    $ git clone https://gitlab.dane.gov.pl/mcod/backend.git
    $ cd backend
    $ git clone https://gitlab.dane.gov.pl/mcod/frontend.git
    $ git clone https://gitlab.dane.gov.pl/mcod/test-data.git

##Uruchomienie kontenerów Docker.

Proces budowania środowiska może trwać nawet kilkadziesiąt minut w zależności od hosta.

    $ docker-compose up -d mcod-db
    $ docker-compose exec mcod-db dropdb mcod --username=mcod
    $ docker-compose exec mcod-db createdb mcod -O mcod --username=mcod
    $ docker-compose exec mcod-db pg_restore -Fc -d mcod /dumps/mcod_db.pgdump --username=mcod
    $ docker-compose up -d mcod-redis mcod-rabbitmq mcod-nginx mcod-elasticsearch-1 mcod-apm  mcod-monitoring mcod-logstash mcod-kibana
    
    $ docker-compose up -d mcod-api
    $ docker-compose up -d mcod-celery mcod-celery-harvester mcod-admin
    
    $ docker-compose exec mcod-api python manage.py search_index --rebuild -f
    $ docker-compose exec mcod-api python manage.py validate_resources --async
    
    $ docker-compose exec mcod-apm apm-server setup -e
    $ docker-compose exec mcod-filebeat filebeat setup -e
    $ docker-compose exec mcod-heartbeat heartbeat setup -e
    $ docker-compose exec mcod-metricbeat metricbeat setup -e

W przypadku korzystania z IDE PyCharm (Professional) możliwe jest dodanie konfiguracji dotyczącej zarządzania kontenerami.

Więcej: https://www.jetbrains.com/help/pycharm/docker-compose.html#working

##Uruchomienie/zatrzymanie usług.

Aby uruchomić wszystkie usługi w katalogu projektu `backend` wykonaj:

    $ docker-compose up -d

Opcjonalnie można uruchamiać tylko wybrane usługi wyspecyfikowane jako parametr polecenia:

    $ docker-compose up -d mcod-db mcod-admin

Aby zatrzymać wybraną usługę, w katalogu projektu `backend` wykonaj:

    $ docker-compose stop mcod-api

Aby zatrzymać usługę łącznie z usunięciem kontenera, w katalogu `backend` wykonaj:

    $ docker-compose down mcod-admin

##Ustawienia lokalne - przypisanie nazw maszyn do kontenera mcod-nginx.

Dodaj mapowanie adresu IP:

    Adres IP: 172.18.18.100

do nazw maszyn:

    mcod.local
    api.mcod.local
    admin.mcod.local
    kibana.mcod.local

## Ręcznie uruchamianie usług

###Panel administracyjny (admin.mcod.local)

    $ docker-compose up -d mcod-admin

Po uruchomieniu usługi, pod adresem http://admin.mcod.local będzie dostępny panel administracyjny ~~(login: admin@mcod.local, hasło: Otwarte.1)~~

###Usługa API (api.mcod.local)

    $ docker-compose up -d mcod-api

###Aplikacja WWW - frontend (mcod.local)

    $ docker-compose up -d mcod-frontend

Po uruchomieniu usługi, po upływie ok 1 minuty, pod adresem http://www.mcod.local bedzie dostępna aplikacja WWW - portal Otwarte Dane.

Do prawidłowego funkcjonowania niezbędne jest uruchomienie usługi API.

### Uruchamianie celery

Uruchomienie usługi jest niezbędne, jeżeli zamierzamy korzystać z zadań asynchronicznych, takich jak wysyłanie mailu czy walidacja plików zasobów.

    $ docker-compose up -d mcod-celery mcod-celery-harvester

## Inne przydatne polecenia.

### Uruchamianie testów jednostkowych

    $ docker-compose up -d mcod-tox

### Reindeksacja wszystkich danych

    $ docker-compose exec mcod-admin python manage.py search_index --rebuild

### Ponowna walidacja zasobu

    $ docker-compose exec mcod-admin python manage.py validate_resources --pks <id_1,...,id_N>

### Zaindeksowanie pliku zasobu (wygenerowanie danych tabelarycznych)

    $ docker-compose exec mcod-admin python manage.py index_file --pks <id_1,...,id_N>
