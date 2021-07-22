/* 3. Usuń trigger i funkcję */
DROP TRIGGER IF EXISTS tg_resource_chart_history ON public.resource_chart;
DROP FUNCTION IF EXISTS public.fn_insert_resource_chart_history();