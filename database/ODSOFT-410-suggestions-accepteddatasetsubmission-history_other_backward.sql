/* 1. TG - suggestions_accepteddatasetsubmission */
DROP TRIGGER IF EXISTS tg_suggestions_accepteddatasetsubmission_history ON public.suggestions_accepteddatasetsubmission;
DROP FUNCTION IF EXISTS public.fn_insert_suggestions_accepteddatasetsubmission_history();
