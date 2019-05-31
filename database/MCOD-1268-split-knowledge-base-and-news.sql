





/* 1. CREATE TRIGGER */
BEGIN;
CREATE OR REPLACE FUNCTION public.fn_insert_article_category_history()
 RETURNS TRIGGER
 LANGUAGE plpgsql
AS $function$

/*
<><><><><><><><><><><><><><><><><><><><><><><><><>
Version:					1.0
Author:						Agnieszka Rutka
Create date:				2019-02-05
Description:				procedura pod trigger - insert do public.History
Last modify by:
Last modified date:
Last update description:
<><><><><><><><><><><><><><><><><><><><><><><><><>
*/



DECLARE
    v_startdatetime               TIMESTAMP;    -- zmienna do logowania czasu startu procedury
    v_enddatetime                 TIMESTAMP;    -- zmienna do logowania czasu końca procedury
    v_datetimediff                INTERVAL;     -- zmienna wewnętrzna, wylicza czas wykonania procedury
    v_functionschema              VARCHAR(255); -- nazwa schematu funkcji
    v_functionname                VARCHAR(255); -- nazwa funkcji
    v_functionfincomingparameters VARCHAR(500); -- wiodące parametry wchodzące
    v_state                       TEXT;         -- kod błędu
    v_columnname                  TEXT;         -- the name of the column related to exception
    v_constraintname              TEXT;         -- the name of the constraint related to exception
    v_pgdatacategoryname          TEXT;         -- the name of the data category related to exception
    v_tablename                   TEXT;         -- the name of the table related to exception
    v_schemaname                  TEXT;         -- the name of the schema related to exception
    v_msg                         TEXT;         -- tekst błędu
    v_detail                      TEXT;         -- szczegóły błędu
    v_hint                        TEXT;         -- podpowiedź do błędu
    v_context                     TEXT;         -- line(s) of text describing the call stack at the time of the exception


BEGIN

    /* ustawienie zmiennych */
    v_startdatetime := clock_timestamp();
    v_functionschema := 'public';
    v_functionname := 'fn_insert_article_category_history';


    /* wstawienie danych do historii */
    IF TG_OP = 'INSERT' THEN

        INSERT INTO public.History
        (
            table_schema, table_name, row_id, "action", new_value, change_user_id
        )
        SELECT
            TG_TABLE_SCHEMA,
            TG_TABLE_NAME,
            NEW.id,
            TG_OP,
            row_to_json(NEW),
        CAST(current_setting('myapp.userid') AS INTEGER);

    ELSIF TG_OP = 'UPDATE' THEN

        INSERT INTO public.History
        (
            table_schema, table_name, row_id, "action", old_value, new_value, change_user_id
        )
        SELECT
            TG_TABLE_SCHEMA,
            TG_TABLE_NAME,
            OLD.id,
            TG_OP,
            row_to_json(OLD),
            row_to_json(NEW),
        CAST(current_setting('myapp.userid') AS INTEGER);

    ELSIF TG_OP = 'DELETE' THEN

        INSERT INTO public.History
        (
            table_schema, table_name, row_id, "action", old_value, change_user_id
        )
        SELECT
            TG_TABLE_SCHEMA,
            TG_TABLE_NAME,
            OLD.id,
            TG_OP,
            row_to_json(OLD),
        CAST(current_setting('myapp.userid') AS INTEGER);

    END IF;


    /* logowanie prawidlowego wywolania procedury */
    v_enddatetime := clock_timestamp();
    v_datetimediff := age(v_enddatetime, v_startdatetime);

    INSERT INTO internals.functions_execute_log
    (
        function_schema, function_name, start_timestamp, end_timestamp, diff_timestamp, incoming_parameters
    )
    SELECT
        v_functionschema,
        v_functionname,
        v_startdatetime,
        v_enddatetime,
        v_datetimediff,
        v_functionfincomingparameters;

    RETURN NEW;


    /* obsługa bledow */
    EXCEPTION
        WHEN OTHERS THEN
            GET STACKED DIAGNOSTICS
                v_state = RETURNED_SQLSTATE,
                v_msg = MESSAGE_TEXT,
                v_detail = PG_EXCEPTION_DETAIL,
                v_hint = PG_EXCEPTION_HINT,
                v_context = PG_EXCEPTION_CONTEXT,
                v_columnname = COLUMN_NAME,
                v_constraintname = CONSTRAINT_NAME,
                v_pgdatacategoryname = PG_DATATYPE_NAME,
                v_tablename = TABLE_NAME,
                v_schemaname = SCHEMA_NAME;


    RAISE NOTICE E'An error occured! Transaction rollbacked!\n RETURNED_SQLSTATE = % \n MESSAGE_TEXT = %\n PG_EXCEPTION_DETAIL = %\n PG_EXCEPTION_HINT = %\n PG_EXCEPTION_CONTEXT = %\n COLUMN_NAME = %\n CONSTRAINT_NAME = %\n PG_DATATYPE_NAME = %\n TABLE_NAME = %\n SCHEMA_NAME = %\n'
    , v_state, v_msg, v_detail, v_hint, v_context, v_columnname, v_constraintname, v_pgdatacategoryname, v_tablename, v_schemaname;

    /* czas końca jeśli był error */
    v_enddatetime := clock_timestamp();
    v_datetimediff := age(v_enddatetime, v_startdatetime);


    INSERT INTO internals.functions_execute_log
    (
        function_schema, function_name, start_timestamp, end_timestamp, diff_timestamp, incoming_parameters, returned_sqlstate, message_text, pg_exception_detail, pg_exception_hint, pg_exception_context, "column_name", "constraint_name", PG_DATATYPE_NAME, "table_name", "schema_name"
    )
    SELECT
        v_functionschema,
        v_functionname,
        v_startdatetime,
        v_enddatetime,
        v_datetimediff,
        v_functionfincomingparameters,
        v_state,
        v_msg,
        v_detail,
        v_hint,
        v_context,
        v_columnname,
        v_constraintname,
        v_pgdatacategoryname,
        v_tablename,
        v_schemaname;

RETURN NULL;

END;
$function$;
COMMIT;

BEGIN;
    CREATE TRIGGER tg_article_category_history
    AFTER INSERT OR DELETE OR UPDATE ON public.article_category FOR EACH ROW EXECUTE PROCEDURE fn_insert_article_category_history();
COMMIT;



/* 2. INSERT INTO DICTIONARY TABLE */
BEGIN;
    INSERT INTO public.article_category
    (
        "name", description, created_by_id, modified_by_id, created, modified
    )
    SELECT 'news', 'Aktualności (dawne artykuły) - zakładka Aktualności', NULL::INTEGER, NULL::INTEGER, now(), now()
    UNION ALL SELECT 'help', 'Pomoc - zakładka Baza wiedzy', NULL::INTEGER, NULL::INTEGER, now(), now()
    UNION ALL SELECT 'training', 'Materiały szkoleniowe - zakładka Baza wiedzy', NULL::INTEGER, NULL::INTEGER, now(), now()
    UNION ALL SELECT 'question', 'Często zadawane pytania - zakładka Baza wiedzy', NULL::INTEGER, NULL::INTEGER, now(), now()
    UNION ALL SELECT 'about', 'O serwisie - stopka portalu', NULL::INTEGER, NULL::INTEGER, now(), now();
COMMIT;



/* 3. UPDATE article TABLE */
ALTER TABLE public.article
    DISABLE TRIGGER tg_article_history;

BEGIN;
    UPDATE public.article
    SET category_id = (SELECT id FROM article_category WHERE "name" = 'news' LIMIT 1)
    WHERE category_id IS NULL;
COMMIT;

ALTER TABLE public.article
    ENABLE TRIGGER tg_article_history;