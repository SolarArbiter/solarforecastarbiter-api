DELETE FROM arbiter_data.organizations WHERE id = UUID_TO_BIN('b76ab62e-4fe1-11e9-9e44-64006a511e6f', 1);
DROP PROCEDURE arbiter_data.insertfx;
DROP PROCEDURE arbiter_data.insertobs;
DROP USER 'apiuser'@'*';
