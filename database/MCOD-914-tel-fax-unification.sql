
/* ORGANIZATION */

/* 1. complete new columns */
UPDATE public.organization
SET tel_internal = TRIM (RIGHT (tel, 3))
WHERE tel ILIKE '%w%';

UPDATE public.organization
SET fax_internal = TRIM (RIGHT (fax, 3))
WHERE fax ILIKE '%w%';



/* 2. unification phone/fax numbers */
UPDATE public.organization
SET tel =
    CASE
        WHEN length(REPLACE (REPLACE (REPLACE (REPLACE (REPLACE(REPLACE (tel, ' ', ''), '+48', ''), '/', ''), '-', ''), ',226959000', ''), '	', '')) = 5
        THEN '004822' || REPLACE (REPLACE (REPLACE (REPLACE (REPLACE(REPLACE (tel, ' ', ''), '+48', ''), '/', ''), '-', ''), ',226959000', ''), '	', '')
        ELSE '0048' || REPLACE (REPLACE (REPLACE (REPLACE (REPLACE(REPLACE (tel, ' ', ''), '+48', ''), '/', ''), '-', ''), ',226959000', ''), '	', '')
    END
WHERE COALESCE (tel, '') <> ''
    AND LEFT(tel, 4) <> '0048';

UPDATE public.organization
SET fax =
    CASE
        WHEN length(REPLACE (REPLACE (REPLACE (REPLACE (REPLACE (REPLACE (REPLACE(REPLACE (fax, ' ', ''), '+48', ''), '/', ''), '-', ''), ',226959000', ''), '	', ''), 'w.30', 'wew.30'), 'wew.', ' wew. ')) = 17
        THEN '0048' || LEFT (REPLACE (REPLACE (REPLACE (REPLACE (REPLACE (REPLACE (REPLACE(REPLACE (fax, ' ', ''), '+48', ''), '/', ''), '-', ''), ',226959000', ''), '	', ''), 'w.30', 'wew.30'), 'wew.', ' wew. '), 9)
        WHEN length(fax) = 4 THEN fax
        ELSE '0048' || REPLACE (REPLACE (REPLACE (REPLACE (REPLACE (REPLACE (REPLACE(REPLACE (fax, ' ', ''), '+48', ''), '/', ''), '-', ''), ',226959000', ''), '	', ''), 'w.30', 'wew.30'), 'wew.', ' wew. ')
    END
WHERE COALESCE (fax, '') <> ''
    AND LEFT(fax, 4) <> '0048'
    AND fax <> 'brak';



/* 3. NULL when no fax */
UPDATE public.organization
SET fax = NULL
WHERE fax IN ('0048', 'brak');



/* USER */
/* 4. complete new columns */
UPDATE public.user
SET tel_internal = TRIM (REPLACE(RIGHT (tel, 3), '.', ''))
WHERE tel ILIKE '%w%';


UPDATE public.user
SET tel = TRIM(SUBSTRING(tel FROM 1 FOR POSITION('w' IN tel)-1))
WHERE tel ILIKE '%w%';



/* 5. unification phone numbers */
;WITH CTE_A AS
(
    SELECT id user_id,
        tel,
        REPLACE (REPLACE (REPLACE (REPLACE (REPLACE (tel, '+48', ''), ' ', ''), '-', ''), '22/', ''), '(22)', '') tel_new
    FROM public.user
    WHERE
        (
            COALESCE (tel, '') <> ''
            OR COALESCE (tel_internal, '') <> ''
        )
        AND LEFT (tel, 4) <> '0048'
)
UPDATE public.user u
SET tel =
    CASE
        WHEN tel_new = '+40227150324' OR tel_new = '0040227150324' THEN '0040227150324'
        WHEN tel_new = '+44225361411' OR tel_new = '0044225361411' THEN '0044225361411'
        WHEN tel_new = '225296415/519319034' THEN '0048225296415'
        WHEN LENGTH(tel_new) IN (5, 7) THEN '004822' || tel_new
        WHEN LENGTH(tel_new) IN (8, 9, 12) THEN '0048' || REPLACE (tel_new, '+48', '')
        ELSE '0048' || tel_new
    END
FROM CTE_A a
WHERE u.id = a.user_id;



/* 6. final checks ORGANIZATION and USER: ALL = 0! */
SELECT
(
    SELECT COUNT(1)
    FROM public.organization
    WHERE LEFT (tel, 4) <> '0048'
)+
(
    SELECT COUNT(1)
    FROM public.organization
    WHERE (LENGTH(tel) <> 13 AND tel <> '00482219115')
)+
(
    SELECT COUNT(1)
    FROM public.organization
    WHERE
    (
        (tel ~ '^[0-9\.]+$') = FALSE
        OR (tel_internal ~ '^[0-9\.]+$') = FALSE
        OR (fax_internal ~ '^[0-9\.]+$') = FALSE
    )
) "organization_if_zero_OK",
(
    SELECT COUNT(1)
    FROM public.user
    WHERE LEFT (tel, 4) NOT IN ('0040', '0044', '0048')
)+
(
    SELECT COUNT(1)
    FROM public.user
    WHERE LENGTH(tel) <> 13
        AND tel <> '004822513562'
)+
(
    SELECT COUNT(1)
    FROM public.user
    WHERE (tel ~ '^[0-9\.]+$') = FALSE
        OR (tel_internal ~ '^[0-9\.]+$') = FALSE
) "user_if_zero_OK";
