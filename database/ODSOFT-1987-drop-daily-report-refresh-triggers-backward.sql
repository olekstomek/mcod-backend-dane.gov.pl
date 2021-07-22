/* 3. CREATE TRIGGERS FOR ALL TABLES USED IN MV */

CREATE TRIGGER tg_refresh_mv_report
AFTER INSERT OR UPDATE OR DELETE
ON public.resource
FOR EACH STATEMENT
EXECUTE PROCEDURE fn_refresh_mv_resource_dataset_organization_report();

CREATE TRIGGER tg_refresh_mv_report
AFTER INSERT OR UPDATE OR DELETE
ON public.dataset
FOR EACH STATEMENT
EXECUTE PROCEDURE fn_refresh_mv_resource_dataset_organization_report();

CREATE TRIGGER tg_refresh_mv_report
AFTER INSERT OR UPDATE OR DELETE
ON public.organization
FOR EACH STATEMENT
EXECUTE PROCEDURE fn_refresh_mv_resource_dataset_organization_report();

CREATE TRIGGER tg_refresh_mv_report
AFTER INSERT OR UPDATE OR DELETE
ON public.user
FOR EACH STATEMENT
EXECUTE PROCEDURE fn_refresh_mv_resource_dataset_organization_report();

CREATE TRIGGER tg_refresh_mv_report
AFTER INSERT OR UPDATE OR DELETE
ON public.user_following_dataset
FOR EACH STATEMENT
EXECUTE PROCEDURE fn_refresh_mv_resource_dataset_organization_report();
