insert into TRLEAS_users_tab(identity, unvan, rowversion, password, aktif,eposta) values
('koray.zorlu', 'Koray Zorlu', sysdate, '1', 1,'koray.zorlu@arileasing.com.tr')

select * from TRLEAS_users_tab

insert into trleas_user_grant_tab(identity, form_name, operation, authorized, description, rowversion)
select 'koray.zorlu', form_name, operation, authorized, description, rowversion from trleas_user_grant_tab
 WHERE identity = 'tarik.corut'