DROP MATERIALIZED VIEW IF EXISTS public.mv_resource_dataset_organization_report;
DROP FUNCTION IF EXISTS fn_refresh_mv_resource_dataset_organization_report();


CREATE MATERIALIZED VIEW public.mv_resource_dataset_organization_report
AS

WITH organizations AS
(
    SELECT
        o.id id_instytucji,
        o.title tytul,
        CASE
            WHEN o.institution_type = 'state' THEN 'administracja rządowa'
            WHEN o.institution_type = 'local' THEN 'administracja samorządowa'
        ELSE o.institution_type
        END rodzaj,
        o.created data_utworzenia_instytucji,
        (
            SELECT COUNT(1)
            FROM public.dataset d
            WHERE o.id = d.organization_id
                AND d.is_removed = FALSE
                AND d.status = 'published'
        ) liczba_udostepnionych_zbiorow_danych
    FROM public.organization o
    WHERE o.is_removed = FALSE
        AND o.status = 'published'
),
datasets AS
(
    SELECT
        o.id id_instytucji,
        d.id id_zbioru_danych,
        d.created data_utworzenia_zbioru_danych,
        d.modified data_modyfikacji_zbioru_danych,
        (
            SELECT COUNT(ud.follower_id)
            FROM public.user_following_dataset ud
                JOIN public.user u ON ud.follower_id = u.id AND u.is_removed = FALSE AND u.state = 'active'
            WHERE ud.dataset_id = d.id
        ) liczba_obserwujacych
    FROM public.organization o
        JOIN public.dataset d ON o.id = d.organization_id
    WHERE o.is_removed = FALSE
        AND o.status = 'published'
        AND d.is_removed = FALSE
        AND d.status = 'published'
),
resources AS
(
    SELECT
        o.id id_instytucji,
        r.id id_zasobu,
        r.title nazwa,
        REPLACE (REPLACE (r.description, '<p>', ''), '</p>', '') opis,
        CASE
            WHEN r.type = 'file' THEN 'plik'
            WHEN r.type = 'website' THEN 'strona internetowa'
        ELSE r.type
        END typ,
        r.format,
        r.created data_utworzenia_zasobu,
        r.modified data_modyfikacji_zasobu,
        r.openness_score stopien_otwartosci,
        r.views_count liczba_wyswietlen,
        r.downloads_count liczba_pobran,
        d.id id_zbioru_danych
    FROM public.organization o
        JOIN public.dataset d ON o.id = d.organization_id
        JOIN public.resource r ON d.id = r.dataset_id
    WHERE o.is_removed = FALSE
        AND o.status = 'published'
        AND d.is_removed = FALSE
        AND d.status = 'published'
        AND r.is_removed = FALSE
        AND r.status = 'published'
)
SELECT
    r.id_zasobu,
    r.nazwa,
    r.opis,
    r.typ,
    r.format,
    r.data_utworzenia_zasobu,
    r.data_modyfikacji_zasobu,
    r.stopien_otwartosci,
    r.liczba_wyswietlen,
    r.liczba_pobran,
    d.id_zbioru_danych,
    d.data_utworzenia_zbioru_danych,
    d.data_modyfikacji_zbioru_danych,
    COALESCE (d.liczba_obserwujacych, 0) liczba_obserwujacych,
    o.id_instytucji,
    o.tytul,
    o.rodzaj,
    o.data_utworzenia_instytucji,
    o.liczba_udostepnionych_zbiorow_danych
FROM organizations o
    LEFT JOIN datasets d ON o.id_instytucji = d.id_instytucji
    LEFT JOIN resources r ON d.id_instytucji = r.id_instytucji AND d.id_zbioru_danych = r.id_zbioru_danych;



/* 2. CREATE TRIGGER FOR REFRESH MATERIALIZED VIEW */

CREATE OR REPLACE FUNCTION fn_refresh_mv_resource_dataset_organization_report()
RETURNS TRIGGER LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_resource_dataset_organization_report;
RETURN NULL;
END $$;

REFRESH MATERIALIZED VIEW mv_resource_dataset_organization_report;
