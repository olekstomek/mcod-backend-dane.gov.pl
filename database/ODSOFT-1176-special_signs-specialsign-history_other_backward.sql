/* Usuń trigger i funkcję */
DROP TRIGGER IF EXISTS tg_special_signs_specialsign_history ON public.special_signs_specialsign;
DROP FUNCTION IF EXISTS public.fn_insert_special_signs_specialsign_history();
