
/* 1. DROP MATERIALIZED VIEW AND TRIGGERS */
DROP MATERIALIZED VIEW IF EXISTS public.mv_resource_dataset_organization_report;
DROP TRIGGER IF EXISTS tg_refresh_mv_report ON public.resource;
DROP TRIGGER IF EXISTS tg_refresh_mv_report ON public.dataset;
DROP TRIGGER IF EXISTS tg_refresh_mv_report ON public.organization;
DROP TRIGGER IF EXISTS tg_refresh_mv_report ON public.user;
DROP TRIGGER IF EXISTS tg_refresh_mv_report ON public.user_following_dataset;
DROP FUNCTION IF EXISTS fn_refresh_mv_resource_dataset_organization_report();
