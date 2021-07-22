/* Usuń trigger i funkcję */
DROP TRIGGER IF EXISTS tg_guides_guide_history ON public.guides_guide;
DROP FUNCTION IF EXISTS public.fn_insert_guides_guide_history();
