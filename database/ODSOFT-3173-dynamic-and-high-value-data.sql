DROP MATERIALIZED VIEW IF EXISTS public.mv_resource_dataset_organization_report_d_hv_data;

CREATE MATERIALIZED VIEW public.mv_resource_dataset_organization_report_d_hv_data
AS

WITH organizations AS
(
    SELECT
        o.id id_instytucji,
        o.title tytul,
        CASE
            WHEN o.institution_type = 'state' THEN 'administracja rządowa'
            WHEN o.institution_type = 'local' THEN 'administracja samorządowa'
            WHEN o.institution_type = 'private' THEN 'podmioty prywatne'
            WHEN o.institution_type = 'other' THEN 'inne'
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
        ) liczba_obserwujacych,
        CASE
            WHEN d.has_high_value_data = TRUE THEN 'TAK'
            WHEN d.has_high_value_data = FALSE THEN 'NIE'
            ELSE 'Nie sprecyzowano'
        END zbior_danych_posiada_dane_wysokiej_wartosci,
        CASE
            WHEN d.has_dynamic_data = TRUE THEN 'TAK'
            WHEN d.has_dynamic_data = FALSE THEN 'NIE'
            ELSE 'Nie sprecyzowano'
        END zbior_danych_posiada_dane_dynamiczne
    FROM public.organization o
        JOIN public.dataset d ON o.id = d.organization_id
    WHERE o.is_removed = FALSE
        AND o.status = 'published'
        AND d.is_removed = FALSE
        AND d.status = 'published'
),
resource_counters AS
(
    SELECT
        r.id id_zasobu,
        (SELECT COALESCE(SUM(rvc.count), 0) FROM public.counters_resourceviewcounter rvc WHERE rvc.resource_id = r.id ) liczba_wyswietlen,
        (SELECT COALESCE(SUM(rdc.count), 0) FROM public.counters_resourcedownloadcounter rdc WHERE rdc.resource_id = r.id ) liczba_pobran
    FROM public.resource r
        LEFT JOIN public.counters_resourceviewcounter rvc ON r.id = rvc.resource_id
        LEFT JOIN public.counters_resourcedownloadcounter rdc ON r.id = rdc.resource_id
    WHERE
        r.is_removed = FALSE
        AND r.status = 'published'
    GROUP BY
        r.id
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
        (SELECT
            string_agg(CASE WHEN rf.format = 'jsonld' THEN 'json-ld' ELSE rf.format END, ', ')
        FROM public.resources_resourcefile rf
        WHERE
            rf.resource_id = r.id
            AND rf.is_main = FALSE)  formaty_po_konwersji,
        r.created data_utworzenia_zasobu,
        r.modified data_modyfikacji_zasobu,
        r.openness_score stopien_otwartosci,
        CASE
            WHEN r.has_high_value_data = TRUE THEN 'TAK'
            WHEN r.has_high_value_data = FALSE THEN 'NIE'
            ELSE 'Nie sprecyzowano'
        END zasob_posiada_dane_wysokiej_wartosci,
        CASE
            WHEN r.has_dynamic_data = TRUE THEN 'TAK'
            WHEN r.has_dynamic_data = FALSE THEN 'NIE'
            ELSE 'Nie sprecyzowano'
        END zasob_posiada_dane_dynamiczne,
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
    r.formaty_po_konwersji,
    r.data_utworzenia_zasobu,
    r.data_modyfikacji_zasobu,
    r.stopien_otwartosci,
    r.zasob_posiada_dane_wysokiej_wartosci,
    r.zasob_posiada_dane_dynamiczne,
    rc.liczba_wyswietlen,
    rc.liczba_pobran,
    d.id_zbioru_danych,
    d.zbior_danych_posiada_dane_wysokiej_wartosci,
    d.zbior_danych_posiada_dane_dynamiczne,
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
    LEFT JOIN resources r ON d.id_instytucji = r.id_instytucji AND d.id_zbioru_danych = r.id_zbioru_danych
    LEFT JOIN resource_counters rc ON r.id_zasobu = rc.id_zasobu;