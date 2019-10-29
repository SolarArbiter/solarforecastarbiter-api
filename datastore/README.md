# Datastore

This folder contains files to setup and test a MySQL database for storing
arbiter data. The migrations folder contains SQL code to create the tables,
triggers, functions, and procedures required. We currently use
[migrate](https://github.com/golang-migrate/migrate) to manage the application
of the SQL files. We follow the [OWASP](https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.md)
best practices to prevent SQL injection attacks.


## Database achitecture
The database has a number of tables to store sites, forecasts,
observations, and access controls for those objects. On-disk encryption
is enabled for all tables, and backups are also encrypted. Indexes on each
table are chosen based on the anticipated workflow. Foreign keys are also
set in order to delete or restrict deletion of resources that have references
across multiple tables. The database will only be accessed from the API by
calling predefined, tested procedures. This will limit the set of database
queries and enforce RBAC on each call.


## Testing
A ``docker-compose.yml`` file is provided to start a database and apply the
migrations for testing. Tests are written in python with pytest.

Test values exist inside of the migration file `0016_test_data.up.sql`, it is a
dump of the values tables of the database with demo values loaded.
To update this test data, run the docker
container and an instance of the API and use the API to add new values. Then use
the command `docker exec <Container ID> /usr/bin/mysqldump -u root
--password=testpassword --no-create-info arbiter_data forecasts_values
cdf_forecasts_values observations_values > 0016_test_data.up.sql` to dump a new
copy of the values tables.

- test_authorization.py contains tests for the role based access control
  procedures and functions including tests that ensure the user cannot access
  items for which they do not have permissions.
- test_drops.py contains tests that ensure data is properly removed from mulitple
  tables when appropriate. One example is a test to ensure any forecast values
  are deleted when the corresponding forecast metadata row is deleted.
- test_lists.py contains tests for various procedures that list the objects
  a user has permissions to read.
- test_permission_triggers.py tests that permissions are properly updated
  for permissions that apply to all objects of a particular type in an
  organization.
