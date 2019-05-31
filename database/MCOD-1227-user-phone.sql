
/* 1. ADD NEW COLUMN */
-- zawarte w migracji mcod/users/migrations/0008_auto_20190114_1324.py
-- ALTER TABLE public.user
--     ADD COLUMN tel VARCHAR(50) NULL,
--     ADD COLUMN tel_internal VARCHAR(20) NULL;



/* 2. TMP TABLE */
;WITH CTE_A AS
(
    SELECT id, customfields, customfields::json->>'official_phone' tel, customfields::json->>'telefon służbowy' tel_sluzbowy, customfields::json->>'official_position' stanowisko, customfields::json->>'stanowisko' stanowisko_2
    FROM public.user
    WHERE COALESCE(customfields, '{}') <> '{}'
),
CTE_B AS
(
    SELECT
        REPLACE (REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE 
        (
            CASE 
                WHEN tel = 'Specjalista' THEN stanowisko
                WHEN TRIM(tel) = 'Brak' THEN NULL
                WHEN TRIM(tel_sluzbowy) = '+48' THEN NULL
            ELSE
                CASE WHEN tel IS NULL THEN CASE WHEN tel_sluzbowy = '' THEN NULL ELSE tel_sluzbowy END ELSE tel END
            END, ' ', ''
        ), '+48', ''), '22/', ''), '-', ''), '(', ''), ')', ''), ',', ''), ' ', '') telefon,
        *
    FROM CTE_A
)
SELECT *
INTO public.tmp_user_phone
FROM CTE_B
WHERE telefon IS NOT NULL;
-- 456



/* 3. UPDATE NEW COLUMNS */
UPDATE public.user u
SET tel_internal = REPLACE (TRIM (RIGHT (d.telefon, 3)), '.', '')
FROM public.tmp_user_phone d
WHERE u.id = d.id
    AND d.telefon ILIKE '%w%';
-- 10


UPDATE public.tmp_user_phone
SET telefon = SUBSTRING(telefon FROM 1 FOR 9)
WHERE telefon ILIKE '%w%';
-- 10


UPDATE public.user u
SET tel =
    CASE
        WHEN length(d.telefon) IN (7) THEN '004822' || d.telefon
        WHEN length(d.telefon) IN (8, 9) THEN '0048' || d.telefon
        WHEN d.telefon = '+40227150324' THEN '0040227150324'
        WHEN d.telefon = '+44225361411' THEN '0044225361411'
        WHEN d.telefon = '225296415/519319034' THEN '0048225296415'
        ELSE d.telefon
    END
FROM public.tmp_user_phone d
WHERE u.id = d.id;
-- 456



/* 3a. CHECK DATA */
SELECT
(
    SELECT COUNT(1) -- 0 - OK
    FROM public.user
    WHERE LEFT (tel, 4) NOT IN ('0040', '0044', '0048')
),
(
    SELECT COUNT(1) -- 0 - OK
    FROM public.user
    WHERE LENGTH(tel) <> 13 AND tel <> '004822513562'
),
(
    SELECT COUNT(1) -- 0 - OK
    FROM public.user
    WHERE (tel ~ '^[0-9\.]+$') = FALSE
        OR (tel_internal ~ '^[0-9\.]+$') = FALSE
);



/* 4. UPDATE history.message */
UPDATE public.history
SET message = 'MCOD-1227 - ujednolicenie nr telefonu'
WHERE table_name IN ('user')
    AND change_user_id = 1
    AND change_timestamp >= CURRENT_DATE
    AND change_timestamp < CURRENT_DATE + INTERVAL '1 day';
    
    

/* 5. DROP TMP TABLE */
DROP TABLE IF EXISTS public.tmp_user_phone;
