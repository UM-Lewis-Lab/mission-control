#! /bin/bash

PGDATABASE="experiment_data" \
PGUSER="$(cat ../database/secrets/postgres-user.secret)" \
PGPASS="$(cat ../database/secrets/postgres-password.secret)" \
"$@"