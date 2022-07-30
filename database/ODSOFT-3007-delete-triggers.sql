DROP TRIGGER IF EXISTS tg_article_dataset_history
ON public.article_dataset;
DROP FUNCTION IF EXISTS public.fn_insert_article_dataset_history();

DROP TRIGGER IF EXISTS tg_reports_report_history
ON public.reports_report;
DROP FUNCTION IF EXISTS public.fn_insert_reports_report_history();

DROP TRIGGER IF EXISTS tg_user_organization_history
ON public.user_organization;
DROP FUNCTION IF EXISTS public.fn_insert_user_organization_history();
