/* Usuń trigger i funkcję */
DROP TRIGGER IF EXISTS tg_academy_course_history ON public.academy_course;
DROP FUNCTION IF EXISTS public.fn_insert_academy_course_history();
