/* 1. TG - suggestions_datasetcomment */
DROP TRIGGER IF EXISTS tg_suggestions_datasetcomment_history ON public.suggestions_datasetcomment;
DROP FUNCTION IF EXISTS public.fn_insert_suggestions_datasetcomment_history();
