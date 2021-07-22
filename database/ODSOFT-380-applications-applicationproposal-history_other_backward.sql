/* Usuń trigger i funkcję */
DROP TRIGGER IF EXISTS tg_applications_applicationproposal_history ON public.applications_applicationproposal;
DROP FUNCTION IF EXISTS public.fn_insert_applications_applicationproposal_history();
