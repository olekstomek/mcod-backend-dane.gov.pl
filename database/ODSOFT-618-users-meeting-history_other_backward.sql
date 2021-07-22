/* 1. TG - users_meeting */
DROP TRIGGER IF EXISTS tg_users_meeting_history ON public.users_meeting;
DROP FUNCTION IF EXISTS public.fn_insert_users_meeting_history();
