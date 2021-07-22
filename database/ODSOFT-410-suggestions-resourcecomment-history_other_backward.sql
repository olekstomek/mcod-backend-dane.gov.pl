/* 1. TG - suggestions_resourcecomment */
DROP TRIGGER IF EXISTS tg_suggestions_resourcecomment_history ON public.suggestions_resourcecomment;
DROP FUNCTION IF EXISTS public.fn_insert_suggestions_resourcecomment_history();
