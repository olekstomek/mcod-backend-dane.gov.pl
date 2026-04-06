# Dokumentacja instalacji i ograniczeń zależności



------------------------------------------------------------------------

# Twarde przypięcia (Hard Pins) i powody

## marshmallow

-   Wersja: `==3.9.1`

- Rozluźnienie ~=3.9 powoduje instalację wersji 3.22 która zwraca błąd:

  ```
  TypeError: metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases
  ```

------------------------------------------------------------------------

## django-celery-beat

-   Wersja: `==2.2.1`

-   Przy użyciu `~=` pojawia się:

    `AttributeError: module 'django.contrib.admin' has no attribute 'action'`

------------------------------------------------------------------------

## django-admin-rangefilter

-   Wersja: `==0.4.0`

-   Po odpięciu wersji:

    `No module named 'rangefilter.filter'`

------------------------------------------------------------------------

## panel

-   Wersja: `~=0.12` wymaga przypięcia zależności `param <2.0`

-- --

## openapi-core

-   Wersja: `==0.7.1`

-   Nowsze wersje powodują:

    `ImportError: cannot import name '_legacy_validators' from 'jsonschema'`

    Niezgodność z nowymi wersjami `jsonschema`.

------------------------------------------------------------------------

## openapi-spec-validator

-   Wersja: `==0.2.9`

-   Nowsze wersje powodują:

    `TypeError: 'type' object is not subscriptable`

------------------------------------------------------------------------

## apispec

-   Wersja: `==1.3.3`
-   j.w.

------------------------------------------------------------------------

## xmlschema

-   Wersja: `==3.4.4`

-   Nowsze wersje powodują błędy walidacji:

    `XMLSchemaValidationError: failed validating 'false' with XsdEnumerationFacets(['False', 'True', ''])`

------------------------------------------------------------------------

## xmlsec i lxml

-   `xmlsec==1.3.14`
-   `lxml==5.3.0`

Nowsze wersje powodują:

`lxml & xmlsec libxml2 library version mismatch`

------------------------------------------------------------------------

## psycopg2-binary

-   Wersja: `==2.8.6`
-   Powód: `database connection isn't set to UTC`

------------------------------------------------------------------------

# Inne ograniczenia wersji

## hypercorn = "~=0.13.2"

- Wersja: `~=0.13.2`
  Efektywnie jest to zamrożona wersja 0.13 (aktualna to 0.18), ale pozostajemy otwarci na np. security patche dla wersji
  0.13.x.
- Powód: [kolejna](https://github.com/pgjones/hypercorn/blob/main/CHANGELOG.rst#0140-2022-08-29) wersja kończy wsparcie
  dla ASGI-2. Efektem są błędy:

```text
[2026-03-18 14:33:59 +0100] [61] [ERROR] Error in ASGI Framework
...
TypeError: __call__() takes 2 positional arguments but 3 were given
```

Sprawdzić możliwość podniesienia wersja po upgrade Django.
------------------------------------------------------------------------
