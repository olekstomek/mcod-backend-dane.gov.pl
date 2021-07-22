/* 3. TG - newsletter_subscription */
DROP TRIGGER IF EXISTS tg_newsletter_subscription_history ON public.newsletter_subscription;
DROP FUNCTION IF EXISTS public.fn_insert_newsletter_subscription_history();

/* 2. TG - newsletter_submission */
DROP TRIGGER IF EXISTS tg_newsletter_submission_history ON public.newsletter_submission;
DROP FUNCTION IF EXISTS public.fn_insert_newsletter_submission_history();

/* 1. TG - newsletter */
DROP TRIGGER IF EXISTS tg_newsletter_history ON public.newsletter;
DROP FUNCTION IF EXISTS public.fn_insert_newsletter_history();
