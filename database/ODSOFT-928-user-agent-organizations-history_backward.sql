/* 1. TG - user_agent_organizations */
DROP TRIGGER IF EXISTS tg_user_agent_organizations_history ON public.user_agent_organizations;
DROP FUNCTION IF EXISTS public.fn_insert_user_agent_organizations_history();
