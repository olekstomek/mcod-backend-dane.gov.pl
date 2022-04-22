SET myapp.userid = 1;
begin;

update "user" set email = 'testmail+user' || id || '@dane.gov.pl';
update "user" set fullname = translate(fullname, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZC', 'xaaaaawiwiqihhasdgkkkkkjhhLLKKJJJJUUUUOOOOPPPPZZZZZZZ');

update "application" set author = translate(author, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZC', 'xaaaaawiwiqihhasdgkkkkkjhhLLKKJJJJUUUUOOOOPPPPZZZZZZZ');
update "article" set author = translate(author, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZC', 'xaaaaawiwiqihhasdgkkkkkjhhLLKKJJJJUUUUOOOOPPPPZZZZZZZ');

update "newsletter_subscription" set email = translate(email, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZC', 'xaaaaawiwiqihhasdgkkkkkjhhLLKKJJJJUUUUOOOOPPPPZZZZZZZ') || '.dane.gov.pl';

update "dataset" set update_notification_recipient_email = 'notification+user' || id || '@dane.gov.pl';

update "showcase" set author = translate(author, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZC', 'xaaaaawiwiqihhasdgkkkkkjhhLLKKJJJJUUUUOOOOPPPPZZZZZZZ');

update "harvester_datasource" set emails = translate(emails, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZC', 'xaaaaawiwiqihhasdgkkkkkjhhLLKKJJJJUUUUOOOOPPPPZZZZZZZ');

update "showcases_showcaseproposal" set author = translate(author, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZC', 'xaaaaawiwiqihhasdgkkkkkjhhLLKKJJJJUUUUOOOOPPPPZZZZZZZ');

update "showcases_showcaseproposal" set applicant_email = translate(applicant_email, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZC', 'xaaaaawiwiqihhasdgkkkkkjhhLLKKJJJJUUUUOOOOPPPPZZZZZZZ') || '.dane.gov.pl';

commit;

