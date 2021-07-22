/* 1. TG - suggestions_datasetsubmission */
DROP TRIGGER IF EXISTS tg_suggestions_datasetsubmission_history ON public.suggestions_datasetsubmission;
DROP FUNCTION IF EXISTS public.fn_insert_suggestions_datasetsubmission_history();
