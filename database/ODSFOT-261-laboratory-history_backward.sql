/* Usuń trigger i funkcję */
DROP TRIGGER IF EXISTS tg_labevents_history ON public.lab_event;
DROP FUNCTION IF EXISTS public.fn_insert_laboratory_history();
