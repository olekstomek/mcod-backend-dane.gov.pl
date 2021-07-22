/* Usuń trigger i funkcję */
DROP TRIGGER IF EXISTS tg_guides_guideitem_history ON public.guides_guideitem;
DROP FUNCTION IF EXISTS public.fn_insert_guides_guideitem_history();
