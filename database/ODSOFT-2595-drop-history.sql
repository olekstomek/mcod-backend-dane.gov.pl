/* triggers from "patches" directory. */
DROP TRIGGER IF EXISTS tg_application_history
ON public.application;
DROP FUNCTION IF EXISTS public.fn_insert_application_history();

DROP TRIGGER IF EXISTS tg_application_tag_history
ON public.application_tag;
DROP FUNCTION IF EXISTS public.fn_insert_application_tag_history();

DROP TRIGGER IF EXISTS tg_application_dataset_history
ON public.application_dataset;
DROP FUNCTION IF EXISTS public.fn_insert_application_dataset_history();

DROP TRIGGER IF EXISTS tg_article_history
ON public.article;
DROP FUNCTION IF EXISTS public.fn_insert_article_history();

DROP TRIGGER IF EXISTS tg_article_tag_history
ON public.article_tag;
DROP FUNCTION IF EXISTS public.fn_insert_article_tag_history();

DROP TRIGGER IF EXISTS tg_dataset_history
ON public.dataset;
DROP FUNCTION IF EXISTS public.fn_insert_dataset_history();

DROP TRIGGER IF EXISTS tg_dataset_tag_history
ON public.dataset_tag;
DROP FUNCTION IF EXISTS public.fn_insert_dataset_tag_history();

DROP TRIGGER IF EXISTS tg_resource_history
ON public.resource;
DROP FUNCTION IF EXISTS public.fn_insert_resource_history();

DROP TRIGGER IF EXISTS tg_category_history
ON public.category;
DROP FUNCTION IF EXISTS public.fn_insert_category_history();

DROP TRIGGER IF EXISTS tg_organization_history
ON public.organization;
DROP FUNCTION IF EXISTS public.fn_insert_organization_history();

DROP TRIGGER IF EXISTS tg_user_history
ON public.user;
DROP FUNCTION IF EXISTS public.fn_insert_user_history();

DROP TRIGGER IF EXISTS tg_user_following_application_history
ON public.user_following_application;
DROP FUNCTION IF EXISTS public.fn_insert_user_following_application_history();

DROP TRIGGER IF EXISTS tg_user_following_article_history
ON public.user_following_article;
DROP FUNCTION IF EXISTS public.fn_insert_user_following_article_history();

DROP TRIGGER IF EXISTS tg_user_following_dataset_history
ON public.user_following_dataset;
DROP FUNCTION IF EXISTS public.fn_insert_user_following_dataset_history();

DROP TRIGGER IF EXISTS tg_tag_history
ON public.tag;
DROP FUNCTION IF EXISTS public.fn_insert_tag_history();

/* triggers from MCOD-1242-watchers_history_other.sql */
DROP TRIGGER IF EXISTS tg_watchers_notification_history ON public.watchers_notification;
DROP FUNCTION IF EXISTS public.fn_insert_watchers_notification_history();

DROP TRIGGER IF EXISTS tg_watchers_subscription_history ON public.watchers_subscription;
DROP FUNCTION IF EXISTS public.fn_insert_watchers_subscription_history();

DROP TRIGGER IF EXISTS tg_watchers_watcher_history ON public.watchers_watcher;
DROP FUNCTION IF EXISTS public.fn_insert_watchers_watcher_history();

/* triggers from MCOD-1268-split-knowledge-base-and-news.sql */
DROP TRIGGER IF EXISTS tg_article_category_history ON public.article_category;
DROP FUNCTION IF EXISTS public.fn_insert_article_category_history();

/* triggers from MCOD-1519-harvester-history_other.sql */
DROP TRIGGER IF EXISTS tg_harvester_datasource_history ON public.harvester_datasource;
DROP FUNCTION IF EXISTS public.fn_insert_harvester_datasource_history();

/* triggers from MCOD-1608-newsletter-history_other.sql */
DROP TRIGGER IF EXISTS tg_newsletter_subscription_history ON public.newsletter_subscription;
DROP FUNCTION IF EXISTS public.fn_insert_newsletter_subscription_history();
DROP TRIGGER IF EXISTS tg_newsletter_submission_history ON public.newsletter_submission;
DROP FUNCTION IF EXISTS public.fn_insert_newsletter_submission_history();
DROP TRIGGER IF EXISTS tg_newsletter_history ON public.newsletter;
DROP FUNCTION IF EXISTS public.fn_insert_newsletter_history();

/* triggers from MCOD-1679-tg-resources-charts-history.sql */
DROP TRIGGER IF EXISTS tg_resource_chart_history ON public.resource_chart;
DROP FUNCTION IF EXISTS public.fn_insert_resource_chart_history();

/* triggers from ODSOFT-100-academy-course-history_other.sql */
DROP TRIGGER IF EXISTS tg_academy_course_history ON public.academy_course;
DROP FUNCTION IF EXISTS public.fn_insert_academy_course_history();

/* triggers from ODSOFT-261-laboratory-history.sql */
DROP TRIGGER IF EXISTS tg_labevents_history ON public.lab_event;
DROP FUNCTION IF EXISTS public.fn_insert_laboratory_history();

/* triggers from ODSOFT-380-applications-applicationproposal-history_other.sql */
DROP TRIGGER IF EXISTS tg_applications_applicationproposal_history ON public.applications_applicationproposal;
DROP FUNCTION IF EXISTS public.fn_insert_applications_applicationproposal_history();

/* triggers from ODSOFT-410-suggestions-accepteddatasetsubmission-history_other.sql */
DROP TRIGGER IF EXISTS tg_suggestions_accepteddatasetsubmission_history ON public.suggestions_accepteddatasetsubmission;
DROP FUNCTION IF EXISTS public.fn_insert_suggestions_accepteddatasetsubmission_history();

/* triggers from ODSOFT-410-suggestions-datasetcomment-history_other.sql */
DROP TRIGGER IF EXISTS tg_suggestions_datasetcomment_history ON public.suggestions_datasetcomment;
DROP FUNCTION IF EXISTS public.fn_insert_suggestions_datasetcomment_history();

/* triggers from ODSOFT-410-suggestions-datasetsubmission-history_other.sql */
DROP TRIGGER IF EXISTS tg_suggestions_datasetsubmission_history ON public.suggestions_datasetsubmission;
DROP FUNCTION IF EXISTS public.fn_insert_suggestions_datasetsubmission_history();

/* triggers from ODSOFT-410-suggestions-resourcecomment-history_other.sql */
DROP TRIGGER IF EXISTS tg_suggestions_resourcecomment_history ON public.suggestions_resourcecomment;
DROP FUNCTION IF EXISTS public.fn_insert_suggestions_resourcecomment_history();

/* triggers from ODSOFT-618-users-meeting-history_other.sql */
DROP TRIGGER IF EXISTS tg_users_meeting_history ON public.users_meeting;
DROP FUNCTION IF EXISTS public.fn_insert_users_meeting_history();

/* triggers from ODSOFT-928-user-agent-organizations_history.sql */
DROP TRIGGER IF EXISTS tg_user_agent_organizations_history ON public.user_agent_organizations;
DROP FUNCTION IF EXISTS public.fn_insert_user_agent_organizations_history();

/* triggers from ODSOFT-1006-guides-guide-history_other.sql */
DROP TRIGGER IF EXISTS tg_guides_guide_history ON public.guides_guide;
DROP FUNCTION IF EXISTS public.fn_insert_guides_guide_history();

/* triggers from ODSOFT-1006-guides-guideitem-history_other.sql */
DROP TRIGGER IF EXISTS tg_guides_guideitem_history ON public.guides_guideitem;
DROP FUNCTION IF EXISTS public.fn_insert_guides_guideitem_history();

/* triggers from ODSOFT-1176-special_signs-specialsign-history_other.sql */
DROP TRIGGER IF EXISTS tg_special_signs_specialsign_history ON public.special_signs_specialsign;
DROP FUNCTION IF EXISTS public.fn_insert_special_signs_specialsign_history();
