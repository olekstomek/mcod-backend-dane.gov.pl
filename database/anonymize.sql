SET myapp.userid = 1;
begin;

update "user" set email = 'testmail+user' || id || '@dane.gov.pl';
update "user" set fullname = translate(fullname, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZC', 'xaaaaawiwiqihhasdgkkkkkjhhLLKKJJJJUUUUOOOOPPPPZZZZZZZ');

update "application" set author = translate(author, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZC', 'xaaaaawiwiqihhasdgkkkkkjhhLLKKJJJJUUUUOOOOPPPPZZZZZZZ');
update "article" set author = translate(author, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZC', 'xaaaaawiwiqihhasdgkkkkkjhhLLKKJJJJUUUUOOOOPPPPZZZZZZZ');

commit;
