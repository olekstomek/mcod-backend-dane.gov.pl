/* 1. TG - harvester_datasource */
DROP TRIGGER IF EXISTS tg_harvester_datasource_history ON public.harvester_datasource;
DROP FUNCTION IF EXISTS public.fn_insert_harvester_datasource_history();
